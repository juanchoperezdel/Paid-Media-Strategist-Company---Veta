"""Sub-Agent 2: Winning & Losing Ads Detector."""

import pandas as pd
from src.agents.base_agent import BaseAgent
from src.utils.metrics import enrich_dataframe


class AdsDetector(BaseAgent):

    def __init__(self, model: str = "claude-sonnet-4-6"):
        super().__init__(
            name="Winning & Losing Ads Detector",
            skill_file="market-ads.md",
            model=model,
        )

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        sections = []
        goals = client_config.get("goals", {})
        sections.append(f"# Ad Performance Analysis: {client_config.get('client_name', 'Unknown')}")
        sections.append(f"Primary KPI: {goals.get('primary_kpi', 'CPA')}")
        sections.append(f"Target CPA: {goals.get('target_cpa', 'N/A')}")
        sections.append(f"Target ROAS: {goals.get('target_roas', 'N/A')}")
        sections.append(f"Creative fatigue threshold: {client_config.get('thresholds', {}).get('creative_fatigue_days', 30)} days")

        for platform, platform_data in data.items():
            if platform.startswith("_"):
                continue

            # Buscar tabs de ads
            for tab_name, df in platform_data.items():
                if df.empty:
                    continue
                if "ad" in tab_name.lower():
                    enriched = enrich_dataframe(df) if self._has_metrics(df) else df
                    sections.append(f"\n## {platform.upper()} - {tab_name}")
                    sections.append(f"Total ads: {len(enriched)}")
                    sections.append(enriched.to_string(index=False, max_rows=200))

            # También incluir campaigns para contexto
            for tab_name, df in platform_data.items():
                if df.empty:
                    continue
                if "campaign" in tab_name.lower():
                    sections.append(f"\n## {platform.upper()} - {tab_name} (context)")
                    sections.append(df.to_string(index=False, max_rows=50))

        sections.append("\nAnalyze these ads and provide your findings in the required JSON format.")
        return "\n".join(sections)

    def _has_metrics(self, df: pd.DataFrame) -> bool:
        metric_cols = {"cost", "clicks", "impressions", "conversions"}
        return len(metric_cols.intersection(set(df.columns))) >= 2

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "winning_ads": [],
            "losing_ads": [],
            "fatigue_alerts": [],
            "overall_creative_health": "unknown",
            "recommendations": [],
            "raw_response": response_text,
        }
