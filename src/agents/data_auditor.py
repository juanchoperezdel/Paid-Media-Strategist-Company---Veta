"""Sub-Agent 4: Data Integrity Auditor."""

import pandas as pd
from src.agents.base_agent import BaseAgent


class DataAuditor(BaseAgent):

    def __init__(self, model: str = "claude-sonnet-4-6"):
        super().__init__(
            name="Data Integrity Auditor",
            skill_file="market-audit-data.md",
            model=model,
        )

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        sections = []
        sections.append(f"# Data Integrity Audit: {client_config.get('client_name', 'Unknown')}")

        # Recopilar métricas clave de cada plataforma para comparación cruzada
        platform_summaries = {}

        for platform, platform_data in data.items():
            if platform.startswith("_"):
                continue
            sections.append(f"\n## {platform.upper()} Data")
            platform_summaries[platform] = {}

            for tab_name, df in platform_data.items():
                if df.empty:
                    continue
                sections.append(f"\n### {tab_name}")
                sections.append(f"Rows: {len(df)}, Columns: {list(df.columns)}")
                sections.append(df.to_string(index=False, max_rows=100))

                # Extraer totales para comparación cruzada
                for col in ["clicks", "conversions", "cost", "impressions", "sessions"]:
                    if col in df.columns:
                        total = pd.to_numeric(df[col], errors="coerce").sum()
                        platform_summaries[platform][col] = total

        # Comparación cruzada pre-calculada
        cross_platform = self._cross_platform_check(platform_summaries)
        if cross_platform:
            sections.append("\n## Pre-calculated Cross-Platform Comparison")
            sections.append(cross_platform)

        sections.append("\nAudit this data for discrepancies and provide findings in the required JSON format.")
        return "\n".join(sections)

    def _cross_platform_check(self, summaries: dict) -> str:
        """Compara métricas entre plataformas."""
        findings = []

        # Comparar clicks de ads vs sessions de GA4
        for ads_platform in ["google_ads", "meta_ads"]:
            if ads_platform in summaries and "ga4" in summaries:
                ads_clicks = summaries[ads_platform].get("clicks", 0)
                ga4_sessions = summaries["ga4"].get("sessions", 0)

                if ads_clicks > 0 and ga4_sessions > 0:
                    variance = abs(ads_clicks - ga4_sessions) / ads_clicks * 100
                    findings.append(
                        f"- {ads_platform} clicks ({ads_clicks}) vs GA4 sessions ({ga4_sessions}): "
                        f"variance {variance:.1f}%"
                    )

        # Comparar conversiones entre plataformas
        for ads_platform in ["google_ads", "meta_ads"]:
            if ads_platform in summaries and "ga4" in summaries:
                ads_conv = summaries[ads_platform].get("conversions", 0)
                ga4_conv = summaries["ga4"].get("conversions", 0)

                if ads_conv > 0 and ga4_conv > 0:
                    variance = abs(ads_conv - ga4_conv) / ads_conv * 100
                    findings.append(
                        f"- {ads_platform} conversions ({ads_conv}) vs GA4 conversions ({ga4_conv}): "
                        f"variance {variance:.1f}%"
                    )

        return "\n".join(findings) if findings else ""

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "discrepancies": [],
            "tracking_issues": [],
            "data_quality_flags": [],
            "overall_data_health": "unknown",
            "confidence_level": "unknown",
            "recommendations": [],
            "raw_response": response_text,
        }
