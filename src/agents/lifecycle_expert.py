"""Sub-agente: Creative Lifecycle Expert.

Analiza la vida útil de creativos por campaña:
- Detecta fatiga y decay por ad
- Correlaciona ediciones con cambios de performance
- Compara con semanas anteriores
- Recomienda cadencia de producción creativa
"""

import json
import pandas as pd

from src.agents.base_agent import BaseAgent
from src.utils.lifecycle import CreativeLifecycleAnalyzer
from src.data.sqlite_store import SQLiteStore
from src.utils.logger import get_logger

logger = get_logger("veta.agents.lifecycle")


class LifecycleExpert(BaseAgent):

    def __init__(self, model: str = "claude-sonnet-4-6"):
        super().__init__(
            name="Creative Lifecycle Expert",
            skill_file="market-lifecycle.md",
            model=model,
            max_tokens=4096,
        )

    def run_lifecycle(
        self,
        client_name: str,
        ad_daily: pd.DataFrame,
        ad_metadata: pd.DataFrame,
        client_config: dict,
        campaign_id: str | None = None,
        campaign_name: str | None = None,
    ) -> dict:
        """Ejecuta análisis de lifecycle completo para una campaña.

        1. Corre el analyzer con metadata
        2. Lee historial de SQLite
        3. Genera conclusión comparativa
        4. Guarda todo en SQLite
        5. Llama al LLM para interpretar
        """
        analyzer = CreativeLifecycleAnalyzer(client_name)
        store = SQLiteStore(client_name)

        # Guardar data en SQLite
        store.save_ad_daily(ad_daily)
        store.save_ad_metadata(ad_metadata)

        # Correr análisis con correlación de ediciones
        results = analyzer.analyze_with_metadata(ad_daily, ad_metadata)

        if "error" in results:
            return {"error": results["error"], "findings": [], "recommendations": []}

        # Leer conclusión anterior para comparar
        previous_conclusions = store.get_conclusions(months=6, campaign_id=campaign_id)
        previous = previous_conclusions[0] if previous_conclusions else None

        # Generar conclusión textual
        conclusion_text = analyzer.to_conclusion(results, campaign_name or client_name, previous)
        vs_previous = analyzer.to_vs_previous(results, previous)

        # Guardar en SQLite
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")

        store.save_lifecycle_snapshot(date, campaign_id or "", campaign_name or "", results)
        store.save_conclusion(date, campaign_id or "", campaign_name or "", conclusion_text, vs_previous)

        rotation = results.get("optimal_rotation_window", {})
        if rotation.get("recommended_days"):
            store.save_rotation(date, campaign_id or "", campaign_name or "", rotation)

        # Leer historial de rotación para el LLM
        rotation_history = store.get_rotation_history(campaign_id)

        # Preparar data para el LLM
        data = {
            "lifecycle_results": results,
            "conclusion": conclusion_text,
            "vs_previous": vs_previous,
            "rotation_history": rotation_history[-12:],  # últimas 12 semanas
            "previous_conclusions": [c["summary"] for c in previous_conclusions[:4]],
        }

        # Llamar al LLM para interpretación
        llm_result = self.run(data, client_config)

        # Enriquecer con data cruda
        llm_result["lifecycle_results"] = results
        llm_result["conclusion"] = conclusion_text
        llm_result["vs_previous"] = vs_previous

        return llm_result

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        sections = []
        client_name = client_config.get("client_name", "Unknown")

        sections.append(f"# Creative Lifecycle Analysis: {client_name}")

        # Resultados del analyzer
        results = data.get("lifecycle_results", {})
        sections.append(f"\n## Resumen")
        sections.append(f"- Ads analizados: {results.get('total_ads_analyzed', 0)}")
        sections.append(f"- Promedio días activo: {results.get('avg_active_days', 0):.0f}")
        sections.append(f"- Decay promedio: día {results.get('avg_decay_point', '?')}")

        rotation = results.get("optimal_rotation_window", {})
        if rotation.get("recommended_days"):
            sections.append(f"- Ventana de rotación: {rotation['recommended_days']} días (confianza: {rotation.get('confidence')})")

        # Distribución por fase
        phases = results.get("phase_distribution", {})
        sections.append(f"\n## Distribución por fase")
        for phase, count in phases.items():
            sections.append(f"- {phase}: {count} ads")

        # Análisis de ediciones
        edit_analysis = results.get("edit_analysis", {})
        if edit_analysis:
            sections.append(f"\n## Análisis ediciones vs fatiga orgánica")
            sections.append(f"- Ads editados: {edit_analysis.get('edited_count', 0)}")
            sections.append(f"- Ads sin editar: {edit_analysis.get('unedited_count', 0)}")
            if edit_analysis.get("edited_avg_decay"):
                sections.append(f"- Decay promedio editados: día {edit_analysis['edited_avg_decay']:.0f}")
            if edit_analysis.get("unedited_avg_decay"):
                sections.append(f"- Decay promedio no editados: día {edit_analysis['unedited_avg_decay']:.0f}")
            sections.append(f"- Patrón: {edit_analysis.get('pattern', 'N/A')}")

        # Detalle por ad
        all_ads = results.get("all_ads", [])
        if all_ads:
            sections.append(f"\n## Detalle por ad ({len(all_ads)} ads)")
            for ad in all_ads:
                edit = ad.get("edit_correlation", {})
                edit_flag = " [EDITADO]" if edit.get("was_edited") else ""
                cause = f" | causa decay: {edit.get('decay_cause', '?')}" if edit.get("decay_cause") else ""
                sections.append(
                    f"- {ad['ad_name']}{edit_flag}: {ad['total_days_active']}d | "
                    f"fase: {ad['phase']} | fatiga: {ad['fatigue']['score']}/100 | "
                    f"decay día: {ad.get('decay_point_day', '-')}{cause}"
                )
                if edit.get("note"):
                    sections.append(f"  → {edit['note']}")

        # Conclusión generada
        sections.append(f"\n## Conclusión automática")
        sections.append(data.get("conclusion", "N/A"))

        # Comparación con semana anterior
        sections.append(f"\n## vs Semana anterior")
        sections.append(data.get("vs_previous", "Primera semana."))

        # Historial de rotación
        rot_history = data.get("rotation_history", [])
        if rot_history:
            sections.append(f"\n## Historial de ventana de rotación")
            for entry in rot_history[-8:]:
                sections.append(
                    f"- {entry.get('date', '?')}: {entry.get('recommended_days', '?')}d "
                    f"(confianza: {entry.get('confidence', '?')})"
                )

        # Conclusiones anteriores
        prev = data.get("previous_conclusions", [])
        if prev:
            sections.append(f"\n## Conclusiones de semanas anteriores")
            for c in prev:
                sections.append(f"- {c}")

        sections.append(f"\n## Instrucciones")
        sections.append("Analiza toda esta data y respondé en el formato JSON especificado en tu system prompt.")

        return "\n".join(sections)

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "findings": [],
            "rotation_window": {},
            "ads_to_replace": [],
            "production_needs": {},
            "vs_last_week": "",
            "risk_level": "unknown",
            "recommendations": [],
            "raw_response": response_text,
        }
