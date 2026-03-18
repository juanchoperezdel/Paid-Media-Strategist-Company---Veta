"""Generador de reportes en Markdown."""

import os
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger("veta.reports.markdown")


class MarkdownReportGenerator:

    def generate(self, report_data: dict, output_path: str) -> str:
        """Genera un reporte en Markdown a partir de los datos del análisis."""
        client_name = report_data.get("client_name", "Unknown")
        timestamp = report_data.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
        synthesis = report_data.get("synthesis", {})
        agent_results = report_data.get("agent_results", {})

        lines = []
        lines.append(f"# Veta Strategist Report — {client_name}")
        lines.append(f"**Fecha:** {self._format_timestamp(timestamp)}")
        lines.append("")

        # Executive Summary
        exec_summary = synthesis.get("executive_summary", "")
        if exec_summary:
            lines.append("## Executive Summary")
            lines.append(exec_summary)
            lines.append("")

        # Key Insights
        insights = synthesis.get("key_insights", [])
        if insights:
            lines.append("## Key Insights")
            for insight in insights:
                if isinstance(insight, dict):
                    icon = "🔴" if insight.get("impact") == "high" else "🟡" if insight.get("impact") == "medium" else "🟢"
                    lines.append(f"- {icon} **{insight.get('insight', '')}**")
                else:
                    lines.append(f"- {insight}")
            lines.append("")

        # Risk Alerts
        risk_alerts = synthesis.get("risk_alerts", [])
        if risk_alerts:
            lines.append("## Risk Alerts")
            for alert in risk_alerts:
                if isinstance(alert, dict):
                    urgency = alert.get("urgency", "medium").upper()
                    lines.append(f"### [{urgency}] {alert.get('risk', '')}")
                    if alert.get("action"):
                        lines.append(f"**Action:** {alert['action']}")
                    lines.append("")
                else:
                    lines.append(f"- {alert}")
            lines.append("")

        # Performance Changes
        perf_changes = synthesis.get("performance_changes", {})
        if perf_changes:
            lines.append("## Performance Changes")
            improvements = perf_changes.get("improvements", [])
            declines = perf_changes.get("declines", [])
            if improvements:
                lines.append("### Improvements")
                for item in improvements:
                    lines.append(f"- ✅ {item}")
            if declines:
                lines.append("### Declines")
                for item in declines:
                    lines.append(f"- ⚠️ {item}")
            lines.append("")

        # Winning & Losing Ads
        self._add_ads_section(lines, agent_results.get("ads", {}))

        # Creative Gaps
        creative_gaps = synthesis.get("creative_gaps", [])
        if creative_gaps:
            lines.append("## Creative Gaps & Opportunities")
            for gap in creative_gaps:
                lines.append(f"- {gap}")
            lines.append("")

        # Data Issues
        data_issues = synthesis.get("data_issues", [])
        if data_issues:
            lines.append("## Data Issues")
            for issue in data_issues:
                lines.append(f"- {issue}")
            lines.append("")

        # Strategic Recommendations
        recommendations = synthesis.get("strategic_recommendations", [])
        if recommendations:
            lines.append("## Strategic Recommendations")
            for rec in recommendations:
                if isinstance(rec, dict):
                    priority = rec.get("priority", "")
                    lines.append(f"### {priority}. {rec.get('recommendation', '')}")
                    if rec.get("expected_impact"):
                        lines.append(f"- **Expected Impact:** {rec['expected_impact']}")
                    if rec.get("effort"):
                        lines.append(f"- **Effort:** {rec['effort']}")
                    lines.append("")
                else:
                    lines.append(f"- {rec}")
            lines.append("")

        # Action Plan
        action_plan = synthesis.get("action_plan", {})
        if action_plan:
            lines.append("## Action Plan")
            category_labels = {
                "client_requests": "Client Requests",
                "internal_tasks": "Internal Tasks",
                "creative_tasks": "Creative Production",
                "tracking_fixes": "Tracking Fixes",
                "campaign_optimizations": "Campaign Optimizations",
            }
            for key, label in category_labels.items():
                tasks = action_plan.get(key, [])
                if tasks:
                    lines.append(f"### {label}")
                    for task in tasks:
                        lines.append(f"- [ ] {task}")
                    lines.append("")

        # Footer
        lines.append("---")
        lines.append("*Generated by Veta Strategist AI*")

        content = "\n".join(lines)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Reporte Markdown generado: {output_path}")
        return content

    def _add_ads_section(self, lines: list, ads_data: dict):
        """Agrega sección de ads ganadores y perdedores."""
        winning = ads_data.get("winning_ads", [])
        losing = ads_data.get("losing_ads", [])

        if winning or losing:
            lines.append("## Ad Performance")

        if winning:
            lines.append("### Winning Ads")
            for ad in winning[:5]:
                if isinstance(ad, dict):
                    lines.append(f"- **{ad.get('headline_or_creative', 'N/A')}** ({ad.get('platform', '')})")
                    lines.append(f"  - {ad.get('primary_kpi_name', 'KPI')}: {ad.get('primary_kpi_value', 'N/A')}")
                    lines.append(f"  - Why it works: {ad.get('why_it_works', '')}")
                    lines.append(f"  - Action: {ad.get('recommended_action', '')}")
                else:
                    lines.append(f"- {ad}")
            lines.append("")

        if losing:
            lines.append("### Losing Ads")
            for ad in losing[:5]:
                if isinstance(ad, dict):
                    lines.append(f"- **{ad.get('headline_or_creative', 'N/A')}** ({ad.get('platform', '')})")
                    lines.append(f"  - {ad.get('primary_kpi_name', 'KPI')}: {ad.get('primary_kpi_value', 'N/A')}")
                    lines.append(f"  - Why it fails: {ad.get('why_it_fails', '')}")
                    lines.append(f"  - Action: {ad.get('recommended_action', '')}")
                else:
                    lines.append(f"- {ad}")
            lines.append("")

    def _format_timestamp(self, timestamp: str) -> str:
        try:
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            return timestamp
