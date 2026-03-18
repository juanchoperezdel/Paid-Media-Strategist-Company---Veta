"""Chat on-demand — el equipo puede hacer preguntas sobre un cliente.

Soporta dos backends:
- OpenRouter (default) — acceso a muchos modelos, pago por uso barato
- Claude API — fallback
"""

import os
import yaml

from openai import OpenAI
from src.utils.logger import get_logger
from src.web.secrets_helper import get_openrouter_key, get_anthropic_key

logger = get_logger("veta.web.chat")


def load_skill_prompt(skill_name: str) -> str:
    """Carga un skill como system prompt."""
    skill_path = os.path.join("skills", f"{skill_name}.md")
    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def get_chat_config() -> dict:
    """Lee la config de chat desde settings.yaml."""
    try:
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            settings = yaml.safe_load(f)
        return settings.get("chat", {})
    except FileNotFoundError:
        return {}


def get_active_backend() -> str:
    """Retorna qué backend se va a usar."""
    config = get_chat_config()
    backend = config.get("backend", "openrouter")
    if backend == "auto":
        if get_openrouter_key():
            return "openrouter"
        else:
            return "claude"
    return backend


def build_context(client_name: str, client_data: dict, recent_reports: list[dict]) -> str:
    """Construye contexto del cliente para responder preguntas."""
    parts = [f"# Contexto del cliente: {client_name}\n"]

    # Conclusiones de lifecycle desde SQLite (6 meses)
    try:
        from src.data.sqlite_store import SQLiteStore
        store = SQLiteStore(client_name)
        conclusions = store.get_conclusions(months=6)
        if conclusions:
            parts.append("\n## Historial de Lifecycle Creativo (últimas 26 semanas)")
            for c in conclusions[:26]:
                parts.append(f"- **{c['date']}** [{c.get('campaign_name', 'general')}]: {c['summary']}")
                if c.get("vs_previous"):
                    parts.append(f"  → vs anterior: {c['vs_previous']}")

        # Rotación histórica
        rotation_history = store.get_rotation_history()
        if rotation_history:
            parts.append("\n## Evolución ventana de rotación")
            for r in rotation_history[-12:]:
                parts.append(
                    f"- {r['date']} [{r.get('campaign_name', '')}]: "
                    f"{r['recommended_days']}d (confianza: {r['confidence']})"
                )
    except Exception:
        pass

    # Data cruda (CSVs — ads, campañas, métricas granulares)
    raw_data = client_data.pop("_data_cruda", {})
    if raw_data:
        parts.append("\n## Data cruda disponible (CSVs)")
        for dataset_name, df in raw_data.items():
            if hasattr(df, "empty") and not df.empty:
                parts.append(f"\n### {dataset_name} ({len(df)} filas, {len(df.columns)} columnas)")
                parts.append(f"Columnas: {', '.join(df.columns.tolist())}")
                # Para datasets chicos, mostrar todo. Para grandes, resumen + sample.
                if len(df) <= 50:
                    parts.append(df.to_string(index=False))
                else:
                    parts.append(f"\nEstadísticas:\n{df.describe().to_string()}")
                    parts.append(f"\nTop 20 filas:\n{df.head(20).to_string(index=False)}")

    # Reportes existentes (markdown completo — análisis previos)
    local_reports = client_data.pop("_reportes_existentes", {})
    if local_reports:
        parts.append("\n## Análisis previos disponibles")
        for report_name, content in local_reports.items():
            parts.append(f"\n### Reporte: {report_name}")
            parts.append(content)

    # Data de plataformas (DataFrames desde Sheets)
    for platform, datasets in client_data.items():
        parts.append(f"\n## Data de {platform}")
        for name, df in datasets.items():
            if hasattr(df, "empty") and not df.empty:
                parts.append(f"\n### {name} ({len(df)} filas)")
                parts.append(df.describe().to_string())
                parts.append(f"\nPrimeras 5 filas:\n{df.head().to_string()}")

    if recent_reports:
        parts.append("\n## Reportes en Drive")
        for report in recent_reports[:3]:
            parts.append(f"- {report.get('name', 'N/A')} ({report.get('created_time', '')})")

    return "\n".join(parts)


def _build_system_prompt(client_name: str, client_data: dict, recent_reports: list[dict]) -> str:
    """Construye el system prompt completo."""
    skill_prompt = load_skill_prompt("market")
    context = build_context(client_name, client_data, recent_reports)

    return f"""{skill_prompt}

{context}

---
Sos un analista de Paid Media de la agencia Veta. Respondé preguntas sobre el cliente
{client_name} usando la data proporcionada. Sé directo, con datos concretos. Si no tenés
suficiente data para responder con certeza, decilo claramente. Respondé siempre en español.

Reglas:
- Nunca juzgar segmentos de Meta por CPA promedio solo (Breakdown Effect)
- Chequear Learning Phase antes de declarar ganadores/perdedores
- Fluctuación normal: 20-30% diario. Preocupante: >50% sostenido
"""


# ─── OpenRouter (default) ──────────────────────────────────

def _chat_openrouter(
    question: str,
    system: str,
    chat_history: list[dict],
    model: str | None = None,
) -> str:
    """Genera respuesta usando OpenRouter (API compatible con OpenAI)."""
    config = get_chat_config()
    api_key = get_openrouter_key()
    model = model or config.get("openrouter_model", "google/gemini-2.0-flash-001")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    messages = [{"role": "system", "content": system}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": question})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=2048,
        temperature=0.3,
    )

    answer = response.choices[0].message.content
    logger.info(f"OpenRouter response ({model}): {len(answer)} chars")
    return answer


# ─── Claude API (fallback) ─────────────────────────────────

def _chat_claude(
    question: str,
    system: str,
    chat_history: list[dict],
) -> str:
    """Genera respuesta usando Claude API."""
    from anthropic import Anthropic

    api_key = get_anthropic_key()
    client = Anthropic(api_key=api_key)
    messages = list(chat_history)
    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=messages,
    )
    answer = response.content[0].text
    logger.info(f"Claude response: {response.usage.input_tokens}in, {response.usage.output_tokens}out")
    return answer


# ─── Función principal ──────────────────────────────────────

def chat_response(
    question: str,
    client_name: str,
    client_data: dict,
    recent_reports: list[dict],
    chat_history: list[dict],
    force_backend: str | None = None,
) -> str:
    """Genera respuesta a una pregunta on-demand sobre el cliente.

    Backends: openrouter (default), claude
    """
    system = _build_system_prompt(client_name, client_data, recent_reports)

    backend = force_backend or get_active_backend()

    try:
        if backend == "openrouter":
            return _chat_openrouter(question, system, chat_history)
        else:
            return _chat_claude(question, system, chat_history)

    except Exception as e:
        logger.error(f"Chat error ({backend}): {e}")

        # Fallback: openrouter → claude
        fallback = "claude" if backend == "openrouter" else "openrouter"
        try:
            logger.info(f"{backend} falló, intentando {fallback}...")
            if fallback == "openrouter" and get_openrouter_key():
                return _chat_openrouter(question, system, chat_history)
            elif fallback == "claude":
                return _chat_claude(question, system, chat_history)
        except Exception:
            pass

        return f"Error: ningún backend pudo responder. Error original ({backend}): {e}"
