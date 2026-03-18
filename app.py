"""Veta Strategist AI — Web App para el equipo.

Lanzar con:
    streamlit run app.py
"""

import os
import yaml
import pandas as pd
import streamlit as st

from src.web.auth import check_auth, logout
from src.web.chat import chat_response
from src.data.drive_client import DriveClient
from src.data.data_fetcher import DataFetcher
from src.orchestrator import VetaStrategist

# ─── Config de página ───────────────────────────────────────
st.set_page_config(
    page_title="Veta Strategist AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── Inyectar CSS custom ────────────────────────────────────
def inject_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

inject_css()


# ─── HTML Helpers para cards ─────────────────────────────────

def card_start(gradient=None):
    """Abre un div de card. gradient: 'blue', 'pink', 'green', 'purple', 'orange' o None."""
    cls = f"veta-card-gradient-{gradient}" if gradient else "veta-card"
    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)

def card_end():
    st.markdown('</div>', unsafe_allow_html=True)

def metric_card(value, label, sublabel=None, gradient=None):
    """Renderiza una métrica grande estilo dashboard."""
    cls = f"veta-card-gradient-{gradient}" if gradient else "veta-card"
    sub_html = f'<div class="veta-metric-sublabel">{sublabel}</div>' if sublabel else ""
    st.markdown(f'''
    <div class="{cls}">
        <div class="veta-metric-big">{value}</div>
        <div class="veta-metric-label">{label}</div>
        {sub_html}
    </div>
    ''', unsafe_allow_html=True)

def progress_bar(name, value, max_val=100, color="blue"):
    """Barra de progreso estilizada."""
    pct = min((value / max_val) * 100, 100) if max_val > 0 else 0
    st.markdown(f'''
    <div class="veta-progress-container">
        <div class="veta-progress-label">
            <span class="veta-progress-name">{name}</span>
            <span class="veta-progress-value">{value:.0f}%</span>
        </div>
        <div class="veta-progress-bar">
            <div class="veta-progress-fill {color}" style="width: {pct}%"></div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def alert_card(text, level="medium"):
    """Alerta estilizada. level: 'high', 'medium', 'low'."""
    st.markdown(f'<div class="veta-alert-{level}">{text}</div>', unsafe_allow_html=True)

def badge(text, color="blue"):
    """Badge/tag inline."""
    return f'<span class="veta-badge veta-badge-{color}">{text}</span>'


# ─── Helpers ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_settings():
    with open("config/settings.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@st.cache_data(ttl=300)
def load_clients_list():
    """Carga la lista de clientes desde config/clients/."""
    clients = {}
    clients_dir = "config/clients"
    if not os.path.exists(clients_dir):
        return clients

    for filename in os.listdir(clients_dir):
        if not filename.endswith(".yaml") or filename.startswith("ejemplo"):
            continue
        filepath = os.path.join(clients_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if config and config.get("active", False):
            clients[config["client_name"]] = {
                "config_path": filepath,
                "config": config,
            }
    return clients


def _load_local_reports(client_name: str) -> dict[str, str]:
    """Lee los reportes markdown existentes en output/ para un cliente."""
    reports = {}
    possible_dirs = [
        os.path.join("output", client_name.lower()),
        os.path.join("output", client_name.lower().replace(" ", "_")),
        os.path.join("output", client_name),
    ]
    for base_dir in possible_dirs:
        if not os.path.exists(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if f.endswith(".md") and f != "README.md":
                    filepath = os.path.join(root, f)
                    try:
                        with open(filepath, "r", encoding="utf-8") as fh:
                            content = fh.read()
                        rel_path = os.path.relpath(filepath, "output")
                        reports[rel_path] = content
                    except Exception:
                        pass
    return reports


def get_drive_client():
    """Obtiene o crea el cliente de Drive."""
    if "drive_client" not in st.session_state:
        try:
            from src.web.secrets_helper import get_google_credentials
            settings = load_settings()
            root_folder = settings.get("drive", {}).get("root_folder_id")
            creds = get_google_credentials()
            st.session_state["drive_client"] = DriveClient(credentials=creds, root_folder_id=root_folder)
        except (FileNotFoundError, Exception) as e:
            print(f"[WARN] Drive no disponible: {e}")
            st.session_state["drive_client"] = None
    return st.session_state["drive_client"]


# ─── Login ──────────────────────────────────────────────────

if not check_auth():
    st.stop()


# ─── Sidebar ────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Veta Strategist AI")

    # Selector de cliente
    clients = load_clients_list()
    if not clients:
        st.warning("No hay clientes configurados. Agregá un YAML en config/clients/")
        st.stop()

    client_name = st.selectbox(
        "Cliente",
        options=list(clients.keys()),
        key="selected_client",
    )

    st.markdown("---")

    # Navegación con iconos
    page = st.radio(
        "Sección",
        options=["📈 Análisis", "💬 Chat", "📄 Reportes", "🗄️ Data", "🔄 Lifecycle"],
        key="page",
    )

    st.markdown("---")

    # Logout
    if st.button("Cerrar sesión", type="secondary", use_container_width=True):
        logout()


# ─── Datos del cliente seleccionado ─────────────────────────

client_info = clients[client_name]
client_config = client_info["config"]
config_path = client_info["config_path"]


# ─── Página: Análisis ──────────────────────────────────────

if page == "📈 Análisis":
    # Welcome header
    st.markdown(f'<div class="veta-welcome">Análisis — {client_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="veta-welcome-sub">Corré análisis de performance para este cliente</div>', unsafe_allow_html=True)

    with st.container(border=True):
        col1, col2 = st.columns(2)

        with col1:
            analysis_type = st.selectbox(
                "Tipo de análisis",
                options=[
                    "Completo (todos los agentes)",
                    "Solo riesgo (rápido)",
                    "Solo Google Ads",
                    "Solo Meta Ads",
                    "Auditoría de data",
                ],
            )

        with col2:
            save_to_drive = st.checkbox("Guardar reporte en Google Drive", value=True)

        if st.button("Correr análisis", type="primary", use_container_width=True):
            with st.spinner("Analizando... esto puede tomar 1-2 minutos"):
                try:
                    strategist = VetaStrategist()

                    # Mapear selección a método
                    if analysis_type == "Completo (todos los agentes)":
                        result = strategist.run_analysis(config_path)
                    elif analysis_type == "Solo riesgo (rápido)":
                        result = strategist.run_analysis(
                            config_path, agents_to_run=["google_expert", "meta_expert", "risk"]
                        )
                    elif analysis_type == "Solo Google Ads":
                        result = strategist.run_google_only(config_path)
                    elif analysis_type == "Solo Meta Ads":
                        result = strategist.run_meta_only(config_path)
                    elif analysis_type == "Auditoría de data":
                        result = strategist.run_analysis(
                            config_path, agents_to_run=["data_audit"]
                        )
                    else:
                        result = strategist.run_analysis(config_path)

                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        synthesis = result.get("synthesis", {})

                        # Resumen ejecutivo en card con gradiente
                        if synthesis.get("executive_summary"):
                            st.markdown("#### Resumen ejecutivo")
                            st.markdown(f'''<div class="veta-card-gradient-blue">
                                {synthesis["executive_summary"]}
                            </div>''', unsafe_allow_html=True)

                        # Alertas de riesgo como alert cards
                        if synthesis.get("risk_alerts"):
                            st.markdown("#### Alertas de riesgo")
                            for alert_item in synthesis["risk_alerts"]:
                                if isinstance(alert_item, dict):
                                    urgency = alert_item.get("urgency", "medium")
                                    level = "high" if urgency == "high" else "medium"
                                    alert_card(alert_item.get("risk", ""), level=level)
                                else:
                                    alert_card(str(alert_item), level="medium")

                        # Recomendaciones en cards individuales
                        if synthesis.get("strategic_recommendations"):
                            st.markdown("#### Recomendaciones")
                            rec_cols = st.columns(min(len(synthesis["strategic_recommendations"]), 3))
                            for i, rec in enumerate(synthesis["strategic_recommendations"]):
                                with rec_cols[i % len(rec_cols)]:
                                    if isinstance(rec, dict):
                                        gradients = ["green", "purple", "orange"]
                                        g = gradients[i % len(gradients)]
                                        impact = rec.get("expected_impact", "")
                                        impact_html = f'<div class="veta-metric-sublabel">{impact}</div>' if impact else ""
                                        st.markdown(f'''<div class="veta-card-gradient-{g}">
                                            <div class="veta-card-title">{rec.get("recommendation", "")}</div>
                                            {impact_html}
                                        </div>''', unsafe_allow_html=True)
                                    else:
                                        st.markdown(f'''<div class="veta-card">
                                            {rec}
                                        </div>''', unsafe_allow_html=True)

                        # Guardar en Drive
                        if save_to_drive:
                            try:
                                drive = get_drive_client()
                                from src.reports.markdown_report import MarkdownReportGenerator
                                gen = MarkdownReportGenerator()
                                md_content = gen.generate(result, f"output/temp_{client_name}.md")
                                doc_url = drive.upload_report_as_doc(client_name, md_content)
                                st.success(f"Reporte guardado en Drive: [Abrir]({doc_url})")
                            except Exception as e:
                                st.warning(f"No se pudo guardar en Drive: {e}")

                        st.success("Análisis completado")

                except Exception as e:
                    st.error(f"Error al correr el análisis: {e}")


# ─── Página: Chat ───────────────────────────────────────────

elif page == "💬 Chat":
    st.markdown(f'<div class="veta-welcome">Chat — {client_name}</div>', unsafe_allow_html=True)

    # Backend info en card sutil
    from src.web.chat import get_active_backend, get_chat_config
    active_backend = get_active_backend()
    config = get_chat_config()
    backend_labels = {
        "openrouter": f"OpenRouter ({config.get('openrouter_model', 'gemini-2.0-flash')})",
        "ollama": f"Ollama local ({config.get('ollama_model', 'llama3.1:8b')})",
        "claude": "Claude API",
    }
    st.markdown(f'''<div class="veta-card" style="padding: 12px 20px; margin-bottom: 16px;">
        <span class="veta-metric-label">Motor: </span>
        <span style="font-weight: 500; color: #1a1a2e;">{backend_labels.get(active_backend, active_backend)}</span>
        <span style="color: #9ca3af; margin-left: 12px;">Hacé preguntas sobre la performance del cliente</span>
    </div>''', unsafe_allow_html=True)

    # Inicializar historial
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Mostrar historial
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input("Ej: ¿Por qué subió el CPA esta semana?"):
        with st.chat_message("user"):
            st.markdown(prompt)

        # Cargar contexto
        recent_reports = []
        client_data = {}

        local_reports_content = _load_local_reports(client_name)
        if local_reports_content:
            client_data["_reportes_existentes"] = local_reports_content

        from src.data.data_fetcher import DataFetcher as DF
        local_csvs = DF.load_local_csvs(client_name)
        if local_csvs:
            client_data["_data_cruda"] = local_csvs

        try:
            drive = get_drive_client()
            recent_reports = drive.list_reports(client_name)
        except Exception:
            pass

        try:
            from src.data.sheets_client import SheetsClient
            settings = load_settings()
            sheets = SheetsClient(settings["google_sheets"]["credentials_file"])
            client_data.update(sheets.load_client_data(client_config))
        except Exception:
            pass

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                answer = chat_response(
                    question=prompt,
                    client_name=client_name,
                    client_data=client_data,
                    recent_reports=recent_reports,
                    chat_history=st.session_state["chat_history"],
                )
                st.markdown(answer)

        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        st.session_state["chat_history"].append({"role": "assistant", "content": answer})

    if st.session_state["chat_history"]:
        if st.button("Limpiar chat", use_container_width=True):
            st.session_state["chat_history"] = []
            st.rerun()


# ─── Página: Reportes ──────────────────────────────────────

elif page == "📄 Reportes":
    st.markdown(f'<div class="veta-welcome">Reportes — {client_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="veta-welcome-sub">Historial de reportes guardados</div>', unsafe_allow_html=True)

    try:
        drive = get_drive_client()
        reports = drive.list_reports(client_name)

        if not reports:
            st.info("No hay reportes guardados todavía para este cliente.")
        else:
            # Grid de cards (3 columnas)
            cols = st.columns(3)
            for i, report in enumerate(reports):
                with cols[i % 3]:
                    date_str = report.get("created_time", "")[:10]
                    url = report.get("url", "")
                    link_html = f'<a href="{url}" target="_blank" style="color: #4A90D9; text-decoration: none; font-weight: 500; font-size: 0.85rem;">Abrir →</a>' if url else ""
                    st.markdown(f'''<div class="veta-report-card">
                        <div class="veta-report-title">{report["name"]}</div>
                        <div class="veta-report-date">{date_str}</div>
                        <div style="margin-top: 12px;">{link_html}</div>
                    </div>''', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error al cargar reportes desde Drive: {e}")
        st.info("Verificá que las credenciales de Google estén configuradas correctamente.")

        # Fallback: reportes locales
        st.markdown("#### Reportes locales")
        output_dir = os.path.join("output", client_name.lower().replace(" ", "_"))
        if os.path.exists(output_dir):
            cols = st.columns(3)
            idx = 0
            for root, dirs, files in os.walk(output_dir):
                for f in sorted(files, reverse=True):
                    if f.endswith(".md"):
                        with cols[idx % 3]:
                            st.markdown(f'''<div class="veta-report-card">
                                <div class="veta-report-title">{f}</div>
                            </div>''', unsafe_allow_html=True)
                        idx += 1
        else:
            st.info("No hay reportes locales tampoco.")


# ─── Página: Data ──────────────────────────────────────────

elif page == "🗄️ Data":
    st.markdown(f'<div class="veta-welcome">Data cruda — {client_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="veta-welcome-sub">Explorá y descargá data de las plataformas</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 Ver data", "⬇️ Bajar data nueva"])

    with tab1:
        from src.data.data_fetcher import DataFetcher as DF
        local_csvs = DF.load_local_csvs(client_name)

        if not local_csvs:
            st.info("No hay data cruda todavía. Usá la pestaña 'Bajar data nueva' para descargarla.")
        else:
            # Mini métricas de datasets
            ds_cols = st.columns(min(len(local_csvs), 4))
            for i, (ds_name, ds_df) in enumerate(local_csvs.items()):
                with ds_cols[i % len(ds_cols)]:
                    metric_card(
                        f"{len(ds_df):,}",
                        ds_name.replace("_", " ").title(),
                        sublabel=f"{len(ds_df.columns)} columnas",
                        gradient=["blue", "green", "purple", "orange"][i % 4],
                    )

            st.markdown("")

            # Selector de dataset
            dataset_name = st.selectbox(
                "Dataset",
                options=list(local_csvs.keys()),
                format_func=lambda x: x.replace("_", " ").title(),
            )

            df = local_csvs[dataset_name]

            # Filtro rápido
            search = st.text_input("Buscar en la tabla (nombre de campaña, ad, etc.)")
            if search:
                mask = df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
                df = df[mask]
                st.caption(f"{len(df)} resultados para '{search}'")

            # Tabla interactiva
            st.dataframe(df, use_container_width=True, height=400)

            # Botón de descarga
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="Descargar CSV",
                data=csv_data,
                file_name=f"{dataset_name}.csv",
                mime="text/csv",
            )

    with tab2:
        st.markdown('''<div class="veta-card" style="padding: 16px 20px;">
            Baja data fresca de las plataformas y la guarda localmente (+ Drive si está configurado).
        </div>''', unsafe_allow_html=True)

        st.markdown("")

        col1, col2 = st.columns(2)
        with col1:
            platforms = st.multiselect(
                "Plataformas",
                options=["Google Ads", "Meta Ads"],
                default=["Google Ads", "Meta Ads"],
            )

        if st.button("Bajar data ahora", type="primary", use_container_width=True):
            with st.spinner("Bajando data de las plataformas..."):
                try:
                    fetcher = DataFetcher()
                    data = fetcher.fetch_all_client_data(client_config)

                    if data:
                        fetcher.save_local(client_name, data)
                        st.success("Data bajada y guardada localmente")

                        try:
                            drive = get_drive_client()
                            fetcher.save_to_drive(drive, client_name, data)
                            st.success("También subida a Google Drive")
                        except Exception:
                            st.info("Drive no configurado — data guardada solo localmente")

                        for platform, datasets in data.items():
                            st.markdown(f"#### {platform.replace('_', ' ').title()}")
                            for name, df_data in datasets.items():
                                if hasattr(df_data, "empty") and not df_data.empty:
                                    st.markdown(f"**{name}**: {len(df_data)} filas")
                                    st.dataframe(df_data.head(), use_container_width=True)
                    else:
                        st.warning("No se pudo bajar data. Verificá las credenciales y IDs de cuenta.")
                except Exception as e:
                    st.error(f"Error bajando data: {e}")


# ─── Página: Lifecycle ─────────────────────────────────────

elif page == "🔄 Lifecycle":
    st.markdown(f'<div class="veta-welcome">Vida útil de creativos — {client_name}</div>', unsafe_allow_html=True)
    st.markdown('<div class="veta-welcome-sub">Analizá cuánto duran los ads antes de decaer. Se refina con cada semana de data.</div>', unsafe_allow_html=True)

    from src.utils.lifecycle import CreativeLifecycleAnalyzer
    from src.data.data_fetcher import DataFetcher as DF
    from src.data.sqlite_store import SQLiteStore

    analyzer = CreativeLifecycleAnalyzer(client_name)
    store = SQLiteStore(client_name)

    # Métricas principales en cards con gradiente
    stats = store.stats()
    if stats["ad_daily_rows"] > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_card(f"{stats['ad_daily_rows']:,}", "Registros diarios", gradient="blue")
        with col2:
            metric_card(str(stats["ad_metadata_rows"]), "Ads trackeados", gradient="green")
        with col3:
            metric_card(str(stats["lifecycle_snapshots"]), "Snapshots", gradient="purple")

        date_range = stats.get("date_range", {})
        if date_range.get("from"):
            st.caption(f"Data desde {date_range['from']} hasta {date_range['to']}")

    st.markdown("")

    # Historial de conclusiones
    conclusions = store.get_conclusions(months=6)
    if conclusions:
        st.markdown("#### Historial de conclusiones")
        for c in conclusions[:8]:
            with st.expander(f"{c['date']} — {c.get('campaign_name', 'general')}"):
                st.markdown(c["summary"])
                if c.get("vs_previous"):
                    st.caption(f"vs anterior: {c['vs_previous']}")

    # Historial de rotación
    rotation_history = store.get_rotation_history()
    if rotation_history:
        st.markdown("#### Evolución de ventana de rotación")
        with st.container(border=True):
            rot_df = pd.DataFrame(rotation_history)
            if "recommended_days" in rot_df.columns:
                st.line_chart(rot_df.set_index("date")["recommended_days"])
            for r in rotation_history[-5:]:
                st.caption(
                    f"{r['date']} [{r.get('campaign_name', '')}]: "
                    f"{r['recommended_days']}d (confianza: {r['confidence']})"
                )

    # Reporte histórico
    report = analyzer.get_lifecycle_report()
    if "Sin datos" not in report:
        with st.container(border=True):
            st.markdown(report)

    # Correr análisis con data disponible
    local_csvs = DF.load_local_csvs(client_name)
    ad_daily_key = None
    ad_meta_key = None
    for key in local_csvs:
        if "ad_daily" in key:
            ad_daily_key = key
        if "ad_meta" in key:
            ad_meta_key = key

    if ad_daily_key:
        ad_daily = local_csvs[ad_daily_key]
        ad_metadata = local_csvs[ad_meta_key] if ad_meta_key else pd.DataFrame()

        st.markdown(f'''<div class="veta-card-gradient-green" style="padding: 12px 20px;">
            Data disponible: <strong>{len(ad_daily)}</strong> registros diarios de ads
        </div>''', unsafe_allow_html=True)

        if st.button("Correr análisis de lifecycle", type="primary", use_container_width=True):
            with st.spinner("Analizando curvas de vida de cada ad..."):
                if not ad_metadata.empty:
                    results = analyzer.analyze_with_metadata(ad_daily, ad_metadata)
                else:
                    results = analyzer.analyze_all_ads(ad_daily)

                if "error" in results:
                    st.warning(results["error"])
                else:
                    # Guardar en SQLite
                    from datetime import datetime as dt
                    date = dt.now().strftime("%Y-%m-%d")
                    store.save_ad_daily(ad_daily)
                    if not ad_metadata.empty:
                        store.save_ad_metadata(ad_metadata)
                    store.save_lifecycle_snapshot(date, "", client_name, results)

                    prev = conclusions[0] if conclusions else None
                    conclusion_text = analyzer.to_conclusion(results, client_name, prev)
                    vs_prev = analyzer.to_vs_previous(results, prev)
                    store.save_conclusion(date, "", client_name, conclusion_text, vs_prev)

                    rotation = results.get("optimal_rotation_window", {})
                    if rotation.get("recommended_days"):
                        store.save_rotation(date, "", client_name, rotation)

                    # Métricas principales en cards con gradiente
                    st.markdown("")
                    m_cols = st.columns(4)
                    with m_cols[0]:
                        metric_card(str(results["total_ads_analyzed"]), "Ads analizados", gradient="blue")
                    with m_cols[1]:
                        metric_card(f"{results['avg_active_days']:.0f}", "Días promedio activo", gradient="green")
                    with m_cols[2]:
                        if rotation.get("recommended_days"):
                            metric_card(f"{rotation['recommended_days']}d", "Rotar cada", gradient="purple")
                        else:
                            metric_card("—", "Rotar cada", sublabel="Insuficiente data", gradient="purple")
                    with m_cols[3]:
                        metric_card(str(results["ads_needing_action"]), "Ads a reemplazar", gradient="orange")

                    if rotation.get("recommended_days"):
                        st.info(rotation["interpretation"])

                    # Análisis de ediciones
                    edit_analysis = results.get("edit_analysis", {})
                    if edit_analysis and edit_analysis.get("pattern"):
                        st.markdown("#### Impacto de ediciones")
                        st.markdown(f'''<div class="veta-card">
                            {edit_analysis["pattern"]}
                        </div>''', unsafe_allow_html=True)

                        ecol1, ecol2 = st.columns(2)
                        with ecol1:
                            decay_info = f"Decay promedio: día {edit_analysis['edited_avg_decay']:.0f}" if edit_analysis.get("edited_avg_decay") else ""
                            metric_card(str(edit_analysis.get("edited_count", 0)), "Ads editados", sublabel=decay_info, gradient="blue")
                        with ecol2:
                            decay_info2 = f"Decay promedio: día {edit_analysis['unedited_avg_decay']:.0f}" if edit_analysis.get("unedited_avg_decay") else ""
                            metric_card(str(edit_analysis.get("unedited_count", 0)), "Ads sin editar", sublabel=decay_info2, gradient="green")

                    # Distribución por fase — barras de progreso estilizadas
                    phase_labels = {
                        "ramp_up": "En aprendizaje",
                        "peak": "Rendimiento óptimo",
                        "plateau": "Estancado",
                        "decline": "Decayendo",
                        "exhausted": "Agotado",
                    }
                    phase_colors = {
                        "ramp_up": "blue",
                        "peak": "green",
                        "plateau": "purple",
                        "decline": "orange",
                        "exhausted": "red",
                    }

                    total_ads = max(results["total_ads_analyzed"], 1)
                    st.markdown("#### Estado de los ads")
                    with st.container(border=True):
                        for phase, count in results["phase_distribution"].items():
                            label = phase_labels.get(phase, phase)
                            color = phase_colors.get(phase, "blue")
                            pct = (count / total_ads) * 100
                            progress_bar(f"{label} ({count})", pct, color=color)

                    # Ads que necesitan acción
                    if results["action_required"]:
                        st.markdown("#### Ads que necesitan reemplazo")
                        for ad in results["action_required"]:
                            fatigue = ad["fatigue"]
                            edit = ad.get("edit_correlation", {})
                            level = "high" if fatigue["level"] == "critical" else "medium"
                            edit_tag = f' {badge("EDITADO", "purple")}' if edit.get("was_edited") else ""
                            cause = f" | Causa: {edit.get('decay_cause', '?')}" if edit.get("decay_cause") else ""

                            alert_card(
                                f"<strong>{ad['ad_name']}</strong>{edit_tag} — {ad['total_days_active']} días — {ad['phase']}{cause}"
                                f"<br><span style='font-size: 0.85rem; color: #6b7280;'>{ad['recommendation']}</span>",
                                level=level,
                            )

                            if edit.get("note"):
                                st.caption(f"  → {edit['note']}")
                            if fatigue["signals"]:
                                for signal in fatigue["signals"]:
                                    st.caption(f"  ↳ {signal}")

                    # Tabla completa
                    st.markdown("#### Detalle de todos los ads")
                    all_ads_df = pd.DataFrame([
                        {
                            "Ad": a["ad_name"],
                            "Días activo": a["total_days_active"],
                            "Fase": phase_labels.get(a["phase"], a["phase"]),
                            "Fatiga": a["fatigue"]["score"],
                            "Decay día": a["decay_point_day"] or "-",
                            "Editado": "Sí" if a.get("edit_correlation", {}).get("was_edited") else "No",
                            "Causa decay": a.get("edit_correlation", {}).get("decay_cause", "-"),
                            "Recomendación": a["recommendation"],
                        }
                        for a in results["all_ads"]
                    ])
                    st.dataframe(all_ads_df, use_container_width=True, height=400)
    else:
        st.info(
            "No hay data diaria de ads todavía. Para generarla:\n"
            "1. Ir a **Data** → **Bajar data nueva**\n"
            "2. El sistema baja insights diarios por ad automáticamente\n"
            "3. Volvé acá y corré el análisis"
        )
