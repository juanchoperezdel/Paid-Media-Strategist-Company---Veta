"""Orquestador principal de Veta Strategist AI.

Arquitectura dual-platform: agentes especializados por plataforma (Google Ads Expert,
Meta Ads Expert) + agentes transversales (Risk, Creative, Data Audit, Tasks).
Todas las acciones son propuestas para revisión humana — nunca se ejecutan automáticamente.
"""

import os
import yaml
from datetime import datetime
from pathlib import Path

from src.data.sheets_client import SheetsClient
from src.agents.google_ads_expert import GoogleAdsExpert
from src.agents.meta_ads_expert import MetaAdsExpert
from src.agents.lifecycle_expert import LifecycleExpert
from src.agents.historical_analyst import HistoricalAnalyst
from src.agents.ads_detector import AdsDetector
from src.agents.risk_detector import RiskDetector
from src.agents.creative_intel import CreativeIntel
from src.agents.data_auditor import DataAuditor
from src.agents.task_generator import TaskGenerator
from src.reports.synthesizer import Synthesizer
from src.reports.markdown_report import MarkdownReportGenerator
from src.reports.pdf_report import PDFReportGenerator
from src.utils.logger import setup_logger, get_logger

logger = get_logger("veta.orchestrator")


class VetaStrategist:
    """Orquestador principal que coordina agentes especializados por plataforma
    y agentes transversales.

    Flujo:
    1. Platform Experts (parallelizable): Google Ads Expert + Meta Ads Expert
    2. Transversal Agents: Risk, Creative, Data Audit (consumen data + expert output)
    3. Task Generator: consolida todos los hallazgos en tareas accionables
    4. Synthesizer: genera reporte estratégico consolidado

    IMPORTANTE: Todas las acciones propuestas requieren aprobación humana.
    """

    def __init__(self, settings_path: str = "config/settings.yaml"):
        self.settings = self._load_settings(settings_path)
        self.sheets_client = SheetsClient(
            self.settings["google_sheets"]["credentials_file"]
        )
        self._init_agents()
        self._init_reports()

    def _load_settings(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _get_model(self, tier: str) -> str:
        return self.settings["anthropic"]["models"].get(tier, "claude-sonnet-4-6")

    def _init_agents(self):
        default_model = self._get_model("default")
        advanced_model = self._get_model("advanced")

        # Platform Expert Agents (new)
        self.platform_experts = {
            "google_expert": GoogleAdsExpert(model=advanced_model),
            "meta_expert": MetaAdsExpert(model=advanced_model),
        }

        # Lifecycle Expert (runs after platform experts, before transversal)
        self.lifecycle_expert = LifecycleExpert(model=default_model)

        # Transversal Agents (existing, now consume expert output)
        self.transversal_agents = {
            "risk": RiskDetector(model=default_model),
            "creative": CreativeIntel(model=advanced_model),
            "data_audit": DataAuditor(model=default_model),
            "tasks": TaskGenerator(model=default_model),
        }

        # Legacy agents (kept for backward compatibility)
        self.legacy_agents = {
            "historical": HistoricalAnalyst(model=default_model),
            "ads": AdsDetector(model=default_model),
        }

        # Combined view for backward compatibility
        self.agents = {
            **self.platform_experts,
            **self.transversal_agents,
            **self.legacy_agents,
        }

    def _init_reports(self):
        self.synthesizer = Synthesizer(model=self._get_model("advanced"))
        self.markdown_generator = MarkdownReportGenerator()
        self.pdf_generator = PDFReportGenerator()

    def load_client_config(self, client_config_path: str) -> dict:
        with open(client_config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def run_analysis(
        self,
        client_config_path: str,
        agents_to_run: list[str] | None = None,
        platforms: list[str] | None = None,
        preloaded_data: dict | None = None,
    ) -> dict:
        """Ejecuta el análisis completo o parcial para un cliente.

        Args:
            client_config_path: ruta al YAML de configuración del cliente
            agents_to_run: lista de agentes a ejecutar. None = todos.
                Opciones: google_expert, meta_expert, risk, creative, data_audit, tasks
                Legacy: historical, ads
            platforms: plataformas a analizar. None = todas las configuradas.
                Opciones: google_ads, meta_ads
            preloaded_data: data pre-cargada (ej: desde Drive o data_fetcher).
                Si se pasa, no se lee de Sheets.
        """
        client_config = self.load_client_config(client_config_path)
        client_name = client_config.get("client_name", "Unknown")

        logger.info(f"=== Iniciando análisis para: {client_name} ===")

        # Cargar data: desde preloaded_data o desde Sheets
        if preloaded_data:
            logger.info("Usando data pre-cargada")
            data = preloaded_data
        else:
            logger.info("Cargando data desde Google Sheets...")
            data = self.sheets_client.load_client_data(client_config)

        if not data:
            logger.error("No se pudo cargar data. Abortando.")
            return {"error": "No data loaded"}

        # Detectar plataformas disponibles
        available_platforms = []
        if "google_ads" in data and data["google_ads"]:
            available_platforms.append("google_ads")
        if "meta_ads" in data and data["meta_ads"]:
            available_platforms.append("meta_ads")

        if platforms:
            available_platforms = [p for p in available_platforms if p in platforms]

        logger.info(f"Plataformas disponibles: {available_platforms}")

        # Determinar agentes a correr
        if agents_to_run is None:
            agents_to_run = self._default_agents_for_platforms(available_platforms)

        results = {}

        # === FASE 1: Platform Experts ===
        logger.info("--- Fase 1: Platform Experts ---")

        if "google_expert" in agents_to_run and "google_ads" in available_platforms:
            logger.info("Ejecutando Google Ads Expert...")
            results["google_expert"] = self.platform_experts["google_expert"].run(
                data, client_config
            )

        if "meta_expert" in agents_to_run and "meta_ads" in available_platforms:
            logger.info("Ejecutando Meta Ads Expert...")
            results["meta_expert"] = self.platform_experts["meta_expert"].run(
                data, client_config
            )

        # === FASE 2.5: Lifecycle Expert (Meta only) ===
        if "lifecycle" in agents_to_run and "meta_ads" in available_platforms:
            logger.info("--- Fase 2.5: Lifecycle Expert ---")
            lifecycle_data = data.get("meta_ads_lifecycle", {})
            ad_daily = lifecycle_data.get("ad_daily")
            ad_metadata = lifecycle_data.get("ad_metadata")

            if ad_daily is not None and ad_metadata is not None and not ad_daily.empty:
                import pandas as pd
                results["lifecycle"] = self.lifecycle_expert.run_lifecycle(
                    client_name=client_name,
                    ad_daily=ad_daily if isinstance(ad_daily, pd.DataFrame) else pd.DataFrame(ad_daily),
                    ad_metadata=ad_metadata if isinstance(ad_metadata, pd.DataFrame) else pd.DataFrame(ad_metadata),
                    client_config=client_config,
                )
            else:
                logger.info("Sin data de lifecycle (ad_daily/ad_metadata no disponible)")

        # === FASE 2: Transversal Agents ===
        logger.info("--- Fase 2: Transversal Agents ---")

        # Enrich data with expert results for transversal agents
        enriched_data = {
            **data,
            "_expert_results": {
                k: v for k, v in results.items()
                if k in ("google_expert", "meta_expert")
            },
        }

        for agent_name in ["risk", "creative", "data_audit"]:
            if agent_name in agents_to_run:
                logger.info(f"Ejecutando {agent_name}...")
                results[agent_name] = self.transversal_agents[agent_name].run(
                    enriched_data, client_config
                )

        # Legacy agents (backward compatibility)
        for agent_name in ["historical", "ads"]:
            if agent_name in agents_to_run:
                logger.info(f"Ejecutando legacy agent: {agent_name}...")
                results[agent_name] = self.legacy_agents[agent_name].run(
                    data, client_config
                )

        # === FASE 3: Task Generator ===
        if "tasks" in agents_to_run and results:
            logger.info("--- Fase 3: Task Generator ---")
            other_results = {k: v for k, v in results.items() if k != "tasks"}
            results["tasks"] = self.transversal_agents["tasks"].run(
                {"analysis_results": other_results, **data}, client_config
            )

        # === FASE 4: Synthesizer + Reports ===
        logger.info("--- Fase 4: Synthesis & Reports ---")
        synthesis = self.synthesizer.run(results, client_config)

        # Generar reportes
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.settings["reports"]["output_dir"]
        os.makedirs(output_dir, exist_ok=True)

        report_data = {
            "client_name": client_name,
            "timestamp": timestamp,
            "platforms_analyzed": available_platforms,
            "agents_executed": list(results.keys()),
            "agent_results": results,
            "synthesis": synthesis,
            "human_approval_required": True,
        }

        formats = self.settings["reports"].get("formats", ["markdown"])

        if "markdown" in formats:
            md_path = os.path.join(output_dir, f"{client_name}_{timestamp}.md")
            self.markdown_generator.generate(report_data, md_path)
            logger.info(f"Reporte Markdown: {md_path}")

        if "pdf" in formats:
            pdf_path = os.path.join(output_dir, f"{client_name}_{timestamp}.pdf")
            self.pdf_generator.generate(report_data, pdf_path)
            logger.info(f"Reporte PDF: {pdf_path}")

        logger.info(f"=== Análisis completado para: {client_name} ===")
        logger.info("⚠️  Todas las acciones propuestas requieren aprobación humana antes de ejecutarse.")
        return report_data

    def _default_agents_for_platforms(self, platforms: list[str]) -> list[str]:
        """Retorna la lista de agentes por defecto según las plataformas disponibles."""
        agents = []

        if "google_ads" in platforms:
            agents.append("google_expert")
        if "meta_ads" in platforms:
            agents.append("meta_expert")

        # Lifecycle (solo si hay Meta)
        if "meta_ads" in platforms:
            agents.append("lifecycle")

        # Transversal agents siempre
        agents.extend(["risk", "creative", "data_audit", "tasks"])

        return agents

    def run_daily_check(self, client_config_path: str) -> dict:
        """Ejecuta solo los chequeos diarios (platform experts + risk)."""
        return self.run_analysis(
            client_config_path,
            agents_to_run=["google_expert", "meta_expert", "risk"],
        )

    def run_weekly_report(self, client_config_path: str) -> dict:
        """Ejecuta el reporte semanal completo."""
        return self.run_analysis(client_config_path)

    def run_google_only(self, client_config_path: str) -> dict:
        """Ejecuta análisis solo de Google Ads."""
        return self.run_analysis(
            client_config_path,
            agents_to_run=["google_expert", "risk", "tasks"],
            platforms=["google_ads"],
        )

    def run_meta_only(self, client_config_path: str) -> dict:
        """Ejecuta análisis solo de Meta Ads."""
        return self.run_analysis(
            client_config_path,
            agents_to_run=["meta_expert", "risk", "tasks"],
            platforms=["meta_ads"],
        )

    def run_all_clients(self, agents_to_run: list[str] | None = None) -> dict:
        """Ejecuta el análisis para todos los clientes activos."""
        clients_dir = "config/clients"
        all_results = {}

        for filename in os.listdir(clients_dir):
            if not filename.endswith(".yaml"):
                continue

            config_path = os.path.join(clients_dir, filename)
            config = self.load_client_config(config_path)

            if not config.get("active", False):
                logger.info(f"Cliente '{config.get('client_name')}' inactivo, saltando...")
                continue

            try:
                result = self.run_analysis(config_path, agents_to_run)
                all_results[config.get("client_name", filename)] = result
            except Exception as e:
                logger.error(f"Error con cliente {filename}: {e}")
                all_results[filename] = {"error": str(e)}

        return all_results
