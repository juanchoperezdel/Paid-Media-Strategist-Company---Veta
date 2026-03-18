"""Sub-Agent 1: Historical Performance Analyst."""

import pandas as pd
from src.agents.base_agent import BaseAgent
from src.utils.metrics import enrich_dataframe, pct_change, detect_anomaly, calculate_trend


class HistoricalAnalyst(BaseAgent):

    def __init__(self, model: str = "claude-sonnet-4-6"):
        super().__init__(
            name="Historical Performance Analyst",
            skill_file="market-historical.md",
            model=model,
        )

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        sections = []
        sections.append(f"# Account Analysis: {client_config.get('client_name', 'Unknown')}")
        sections.append(f"Primary KPI: {client_config.get('goals', {}).get('primary_kpi', 'CPA')}")
        sections.append(f"Target CPA: {client_config.get('goals', {}).get('target_cpa', 'N/A')}")
        sections.append(f"Target ROAS: {client_config.get('goals', {}).get('target_roas', 'N/A')}")

        # Procesar data de cada plataforma
        for platform, platform_data in data.items():
            if platform.startswith("_"):
                continue
            sections.append(f"\n## {platform.upper()} Data")

            for tab_name, df in platform_data.items():
                if df.empty:
                    continue
                enriched = enrich_dataframe(df) if self._has_metric_columns(df) else df
                sections.append(f"\n### {tab_name}")
                sections.append(f"Rows: {len(enriched)}")
                sections.append(enriched.to_string(index=False, max_rows=100))

        # Pre-cálculos de anomalías si hay daily metrics
        pre_analysis = self._pre_analyze(data)
        if pre_analysis:
            sections.append("\n## Pre-calculated Anomalies & Trends")
            sections.append(pre_analysis)

        thresholds = client_config.get("thresholds", {})
        sections.append(f"\n## Alert Thresholds")
        for key, val in thresholds.items():
            sections.append(f"- {key}: {val}")

        sections.append("\nAnalyze this data and provide your findings in the required JSON format.")
        return "\n".join(sections)

    def _has_metric_columns(self, df: pd.DataFrame) -> bool:
        metric_cols = {"cost", "clicks", "impressions", "conversions"}
        return len(metric_cols.intersection(set(df.columns))) >= 2

    def _pre_analyze(self, data: dict) -> str:
        """Pre-calcula anomalías y tendencias en datos numéricos."""
        findings = []

        for platform, platform_data in data.items():
            if platform.startswith("_"):
                continue
            for tab_name, df in platform_data.items():
                if df.empty or "daily" not in tab_name.lower():
                    continue

                for col in ["cost", "clicks", "impressions", "conversions", "cpa", "roas", "ctr"]:
                    if col in df.columns:
                        values = pd.to_numeric(df[col], errors="coerce").dropna().tolist()
                        if len(values) >= 7:
                            anomalies = detect_anomaly(values)
                            trend = calculate_trend(values)
                            if anomalies or trend in ("improving", "declining"):
                                findings.append(
                                    f"- {platform}/{tab_name}/{col}: trend={trend}, "
                                    f"anomalies={len(anomalies)}"
                                )

        return "\n".join(findings) if findings else ""

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "findings": [],
            "anomalies": [],
            "trends": [],
            "seasonality": [],
            "fatigue_signals": [],
            "overall_risk_level": "unknown",
            "recommendations": [],
            "raw_response": response_text,
        }
