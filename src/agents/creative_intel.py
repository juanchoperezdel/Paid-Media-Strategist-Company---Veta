"""Sub-Agent 3: Creative Intelligence Agent."""

import pandas as pd
from src.agents.base_agent import BaseAgent
from src.utils.metrics import enrich_dataframe


class CreativeIntel(BaseAgent):

    def __init__(self, model: str = "claude-opus-4-6"):
        super().__init__(
            name="Creative Intelligence Agent",
            skill_file="market-creative.md",
            model=model,
        )

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        sections = []
        goals = client_config.get("goals", {})

        sections.append(f"# Creative Analysis: {client_config.get('client_name', 'Unknown')}")
        sections.append(f"Primary KPI: {goals.get('primary_kpi', 'CPA')}")
        sections.append(f"Industry/Vertical: {client_config.get('industry', 'Not specified')}")

        for platform, platform_data in data.items():
            if platform.startswith("_"):
                continue

            for tab_name, df in platform_data.items():
                if df.empty:
                    continue
                # Priorizar tabs de ads que tengan info de creativos
                if "ad" in tab_name.lower():
                    enriched = enrich_dataframe(df) if self._has_metrics(df) else df
                    sections.append(f"\n## {platform.upper()} - {tab_name}")
                    sections.append(f"Total creatives: {len(enriched)}")
                    sections.append(enriched.to_string(index=False, max_rows=200))

        sections.append("\nAnalyze the creative performance, identify gaps, and generate test ideas in the required JSON format.")
        return "\n".join(sections)

    def _has_metrics(self, df: pd.DataFrame) -> bool:
        metric_cols = {"cost", "clicks", "impressions", "conversions"}
        return len(metric_cols.intersection(set(df.columns))) >= 2

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "internal_analysis": {},
            "creative_gaps": [],
            "market_trends": [],
            "creative_test_ideas": [],
            "recommendations": [],
            "raw_response": response_text,
        }
