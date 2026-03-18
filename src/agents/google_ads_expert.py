"""Platform Expert: Google Ads Expert Agent.

Performs deep analysis of Google Ads campaigns using the STAB framework,
Semaphore audit methodology, and Google Ads reference documents.
All actions are proposals for human review — never auto-executed.
"""

import os
import pandas as pd
from src.agents.base_agent import BaseAgent
from src.utils.metrics import enrich_dataframe, pct_change, detect_anomaly, calculate_trend


class GoogleAdsExpert(BaseAgent):

    def __init__(self, model: str = "claude-sonnet-4-6"):
        super().__init__(
            name="Google Ads Expert",
            skill_file="market-google.md",
            model=model,
            max_tokens=8192,
        )
        self._reference_docs = None

    @property
    def reference_docs(self) -> str:
        """Carga los reference docs de Google Ads para incluir en el prompt."""
        if self._reference_docs is None:
            refs_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "skills", "references",
            )
            docs = []
            google_refs = [
                "google_quality_score.md",
                "google_smart_bidding.md",
                "google_search_terms.md",
                "google_auction_insights.md",
                "google_budget_optimization.md",
                "google_ad_rank.md",
                "google_conversion_tracking.md",
                "google_campaign_types.md",
                "google_performance_fluctuations.md",
                "google_stab_framework.md",
            ]
            for ref_file in google_refs:
                ref_path = os.path.join(refs_dir, ref_file)
                if os.path.exists(ref_path):
                    with open(ref_path, "r", encoding="utf-8") as f:
                        docs.append(f.read())
            self._reference_docs = "\n\n---\n\n".join(docs)
        return self._reference_docs

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        sections = []
        goals = client_config.get("goals", {})
        thresholds = client_config.get("thresholds", {})

        # Header
        sections.append(f"# Google Ads Analysis: {client_config.get('client_name', 'Unknown')}")
        sections.append(f"Primary KPI: {goals.get('primary_kpi', 'CPA')}")
        sections.append(f"Target CPA: {goals.get('target_cpa', 'N/A')}")
        sections.append(f"Target ROAS: {goals.get('target_roas', 'N/A')}")
        sections.append(f"Monthly Budget: {goals.get('monthly_budget', 'N/A')}")

        # Reference knowledge (condensado)
        sections.append("\n## Reference Knowledge")
        sections.append(self.reference_docs)

        # Google Ads data
        google_data = data.get("google_ads", {})
        if not google_data:
            sections.append("\n## WARNING: No Google Ads data available")
            sections.append("Provide analysis recommendations based on available configuration and goals.")
        else:
            for tab_name, df in google_data.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    enriched = enrich_dataframe(df) if self._has_metric_columns(df) else df
                    sections.append(f"\n## Google Ads - {tab_name}")
                    sections.append(f"Rows: {len(enriched)}")
                    sections.append(enriched.to_string(index=False, max_rows=200))

        # Pre-análisis de tendencias y anomalías
        pre_analysis = self._pre_analyze_google(google_data)
        if pre_analysis:
            sections.append("\n## Pre-calculated Anomalies & Trends (Google Ads)")
            sections.append(pre_analysis)

        # Thresholds
        sections.append("\n## Alert Thresholds")
        for key, val in thresholds.items():
            sections.append(f"- {key}: {val}")

        sections.append("\n## IMPORTANT")
        sections.append("All recommended actions are PROPOSALS for human review.")
        sections.append("Format each action as: PROPOSED ACTION → RATIONALE → EXPECTED IMPACT")
        sections.append("\nAnalyze this Google Ads data and provide your findings in the required JSON format.")

        return "\n".join(sections)

    def _has_metric_columns(self, df: pd.DataFrame) -> bool:
        metric_cols = {"cost", "clicks", "impressions", "conversions", "cost_micros"}
        return len(metric_cols.intersection(set(df.columns))) >= 2

    def _pre_analyze_google(self, google_data: dict) -> str:
        """Pre-calcula anomalías y tendencias en datos de Google Ads."""
        findings = []

        for tab_name, df in google_data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            if "daily" not in tab_name.lower() and "metric" not in tab_name.lower():
                continue

            metric_cols = [
                "cost", "clicks", "impressions", "conversions",
                "cpa", "roas", "ctr", "cpc", "impression_share",
                "quality_score", "search_impression_share",
            ]
            for col in metric_cols:
                if col in df.columns:
                    values = pd.to_numeric(df[col], errors="coerce").dropna().tolist()
                    if len(values) >= 7:
                        anomalies = detect_anomaly(values)
                        trend = calculate_trend(values)
                        if anomalies or trend in ("improving", "declining"):
                            findings.append(
                                f"- google_ads/{tab_name}/{col}: trend={trend}, "
                                f"anomalies={len(anomalies)}"
                            )

        # Quality Score distribution si existe
        for tab_name, df in google_data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            if "quality_score" in df.columns:
                qs = pd.to_numeric(df["quality_score"], errors="coerce").dropna()
                if not qs.empty:
                    low = (qs <= 4).sum()
                    mid = ((qs >= 5) & (qs <= 6)).sum()
                    high = (qs >= 7).sum()
                    total = len(qs)
                    findings.append(
                        f"- google_ads/{tab_name}/quality_score_distribution: "
                        f"QS≤4={low} ({low/total*100:.0f}%), "
                        f"QS5-6={mid} ({mid/total*100:.0f}%), "
                        f"QS7+={high} ({high/total*100:.0f}%)"
                    )

        return "\n".join(findings) if findings else ""

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "account_health": {},
            "semaphore_audit": {"green": [], "red": [], "yellow": []},
            "stab_analysis": {},
            "campaign_analysis": [],
            "competitive_landscape": {},
            "scaling_assessment": {},
            "proposed_actions_summary": [],
            "overall_account_health": "unknown",
            "recommendations": [],
            "raw_response": response_text,
        }
