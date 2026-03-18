"""Sub-Agent 5: Risk Detection Agent."""

import pandas as pd
from src.agents.base_agent import BaseAgent
from src.utils.metrics import enrich_dataframe, pct_change, detect_anomaly


class RiskDetector(BaseAgent):

    def __init__(self, model: str = "claude-sonnet-4-6"):
        super().__init__(
            name="Risk Detection Agent",
            skill_file="market-risk.md",
            model=model,
        )

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        sections = []
        goals = client_config.get("goals", {})
        thresholds = client_config.get("thresholds", {})

        sections.append(f"# Risk Assessment: {client_config.get('client_name', 'Unknown')}")
        sections.append(f"Primary KPI: {goals.get('primary_kpi', 'CPA')}")
        sections.append(f"Target CPA: {goals.get('target_cpa', 'N/A')}")
        sections.append(f"Target ROAS: {goals.get('target_roas', 'N/A')}")
        sections.append(f"Monthly Budget: {goals.get('monthly_budget', 'N/A')} {goals.get('currency', 'USD')}")

        sections.append("\n## Alert Thresholds")
        for key, val in thresholds.items():
            sections.append(f"- {key}: {val}")

        # Incluir resultados de Platform Experts si están disponibles
        expert_results = data.get("_expert_results", {})
        if expert_results:
            sections.append("\n## Platform Expert Findings (for cross-platform risk assessment)")
            import json
            for expert_name, result in expert_results.items():
                clean = {k: v for k, v in result.items() if not k.startswith("_")}
                sections.append(f"\n### {expert_name.upper()}")
                sections.append(json.dumps(clean, indent=2, default=str)[:4000])

        # Incluir data con foco en métricas diarias
        for platform, platform_data in data.items():
            if platform.startswith("_"):
                continue
            sections.append(f"\n## {platform.upper()} Data")

            for tab_name, df in platform_data.items():
                if df.empty:
                    continue
                enriched = enrich_dataframe(df) if self._has_metrics(df) else df
                sections.append(f"\n### {tab_name}")
                sections.append(enriched.to_string(index=False, max_rows=100))

        # Pre-detectar señales de riesgo
        risk_signals = self._pre_detect_risks(data, thresholds)
        if risk_signals:
            sections.append("\n## Pre-detected Risk Signals")
            sections.append(risk_signals)

        sections.append("\nAnalyze for risks and provide early warning alerts in the required JSON format.")
        return "\n".join(sections)

    def _has_metrics(self, df: pd.DataFrame) -> bool:
        metric_cols = {"cost", "clicks", "impressions", "conversions"}
        return len(metric_cols.intersection(set(df.columns))) >= 2

    def _pre_detect_risks(self, data: dict, thresholds: dict) -> str:
        """Pre-detección de señales de riesgo basada en umbrales configurados."""
        signals = []

        for platform, platform_data in data.items():
            if platform.startswith("_"):
                continue
            for tab_name, df in platform_data.items():
                if df.empty or "daily" not in tab_name.lower():
                    continue

                # Detectar tendencia de CPA creciente
                if "cpa" in df.columns or ("cost" in df.columns and "conversions" in df.columns):
                    if "cpa" not in df.columns:
                        df = enrich_dataframe(df)
                    if "cpa" in df.columns:
                        cpa_values = pd.to_numeric(df["cpa"], errors="coerce").dropna().tolist()
                        if len(cpa_values) >= 3:
                            recent = cpa_values[-3:]
                            if all(recent[i] > recent[i - 1] for i in range(1, len(recent))):
                                signals.append(f"⚠️ {platform}: CPA rising {len(recent)} consecutive days")

                # Detectar anomalías
                for col in ["ctr", "cpc", "cvr"]:
                    if col in df.columns:
                        values = pd.to_numeric(df[col], errors="coerce").dropna().tolist()
                        anomalies = detect_anomaly(values)
                        for a in anomalies:
                            signals.append(
                                f"⚠️ {platform}/{col}: anomaly at index {a['index']}, "
                                f"value={a['value']}, deviation={a['deviation']}σ ({a['direction']})"
                            )

        return "\n".join(signals) if signals else ""

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "alerts": [],
            "risk_summary": {"critical_count": 0, "high_count": 0, "medium_count": 0, "low_count": 0},
            "overall_risk_level": "unknown",
            "top_3_priorities": [],
            "monitoring_notes": [],
            "raw_response": response_text,
        }
