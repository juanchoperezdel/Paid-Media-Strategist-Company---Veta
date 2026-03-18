"""Platform Expert: Meta Ads Expert Agent.

Performs deep analysis of Meta Ads campaigns using the Andromeda methodology,
Breakdown Effect awareness, and Meta Ads reference documents.
All actions are proposals for human review — never auto-executed.
"""

import os
import pandas as pd
from src.agents.base_agent import BaseAgent
from src.utils.metrics import enrich_dataframe, pct_change, detect_anomaly, calculate_trend


class MetaAdsExpert(BaseAgent):

    def __init__(self, model: str = "claude-sonnet-4-6"):
        super().__init__(
            name="Meta Ads Expert",
            skill_file="market-meta.md",
            model=model,
            max_tokens=8192,
        )
        self._reference_docs = None

    @property
    def reference_docs(self) -> str:
        """Carga los reference docs de Meta Ads para incluir en el prompt."""
        if self._reference_docs is None:
            refs_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "skills", "references",
            )
            docs = []
            meta_refs = [
                "breakdown_effect.md",
                "learning_phase.md",
                "ad_relevance_diagnostics.md",
                "auction_overlap.md",
                "pacing.md",
                "bid_strategies.md",
                "ad_auctions.md",
                "core_concepts.md",
                "performance_fluctuations.md",
                "meta_andromeda_scaling.md",
            ]
            for ref_file in meta_refs:
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
        sections.append(f"# Meta Ads Analysis: {client_config.get('client_name', 'Unknown')}")
        sections.append(f"Primary KPI: {goals.get('primary_kpi', 'CPA')}")
        sections.append(f"Target CPA: {goals.get('target_cpa', 'N/A')}")
        sections.append(f"Target ROAS: {goals.get('target_roas', 'N/A')}")
        sections.append(f"Monthly Budget: {goals.get('monthly_budget', 'N/A')}")

        # Reference knowledge (condensado)
        sections.append("\n## Reference Knowledge")
        sections.append(self.reference_docs)

        # Meta Ads data
        meta_data = data.get("meta_ads", {})
        if not meta_data:
            sections.append("\n## WARNING: No Meta Ads data available")
            sections.append("Provide analysis recommendations based on available configuration and goals.")
        else:
            for tab_name, df in meta_data.items():
                if isinstance(df, pd.DataFrame) and not df.empty:
                    enriched = enrich_dataframe(df) if self._has_metric_columns(df) else df
                    sections.append(f"\n## Meta Ads - {tab_name}")
                    sections.append(f"Rows: {len(enriched)}")
                    sections.append(enriched.to_string(index=False, max_rows=200))

        # Pre-análisis
        pre_analysis = self._pre_analyze_meta(meta_data)
        if pre_analysis:
            sections.append("\n## Pre-calculated Anomalies & Trends (Meta Ads)")
            sections.append(pre_analysis)

        # Thresholds
        sections.append("\n## Alert Thresholds")
        for key, val in thresholds.items():
            sections.append(f"- {key}: {val}")

        sections.append("\n## IMPORTANT")
        sections.append("All recommended actions are PROPOSALS for human review.")
        sections.append("Format each action as: PROPOSED ACTION → RATIONALE → EXPECTED IMPACT")
        sections.append("Apply Andromeda 1 principles: consolidation, GPT over ROAS, new customer focus.")
        sections.append("NEVER judge segment performance by average CPA alone — apply the Breakdown Effect.")
        sections.append("\nAnalyze this Meta Ads data and provide your findings in the required JSON format.")

        return "\n".join(sections)

    def _has_metric_columns(self, df: pd.DataFrame) -> bool:
        metric_cols = {"cost", "spend", "clicks", "impressions", "conversions", "results"}
        return len(metric_cols.intersection(set(df.columns))) >= 2

    def _pre_analyze_meta(self, meta_data: dict) -> str:
        """Pre-calcula anomalías y tendencias en datos de Meta Ads."""
        findings = []

        for tab_name, df in meta_data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            if "daily" not in tab_name.lower() and "metric" not in tab_name.lower():
                continue

            metric_cols = [
                "cost", "spend", "clicks", "impressions", "conversions",
                "results", "cpa", "roas", "ctr", "cpc", "cpm", "frequency",
            ]
            for col in metric_cols:
                if col in df.columns:
                    values = pd.to_numeric(df[col], errors="coerce").dropna().tolist()
                    if len(values) >= 7:
                        anomalies = detect_anomaly(values)
                        trend = calculate_trend(values)
                        if anomalies or trend in ("improving", "declining"):
                            findings.append(
                                f"- meta_ads/{tab_name}/{col}: trend={trend}, "
                                f"anomalies={len(anomalies)}"
                            )

        # Frequency analysis
        for tab_name, df in meta_data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            if "frequency" in df.columns:
                freq = pd.to_numeric(df["frequency"], errors="coerce").dropna()
                if not freq.empty:
                    high_freq = (freq > 3).sum()
                    if high_freq > 0:
                        findings.append(
                            f"- meta_ads/{tab_name}/frequency: "
                            f"{high_freq} ad sets with frequency >3 (saturation risk)"
                        )

        # Learning phase detection
        for tab_name, df in meta_data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue
            if "delivery" in df.columns or "status" in df.columns:
                status_col = "delivery" if "delivery" in df.columns else "status"
                learning = df[df[status_col].astype(str).str.contains("learning", case=False, na=False)]
                if not learning.empty:
                    findings.append(
                        f"- meta_ads/{tab_name}/learning_phase: "
                        f"{len(learning)} ad sets in learning phase"
                    )

        return "\n".join(findings) if findings else ""

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "delivery_status": {},
            "structure_assessment": {},
            "winning_ads": [],
            "losing_ads": [],
            "fatigue_alerts": [],
            "trend_analysis": {},
            "scaling_assessment": {},
            "breakdown_effect_notes": [],
            "proposed_actions_summary": [],
            "overall_account_health": "unknown",
            "recommendations": [],
            "raw_response": response_text,
        }
