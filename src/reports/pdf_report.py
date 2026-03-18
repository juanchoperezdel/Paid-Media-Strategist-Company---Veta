"""Generador de reportes en PDF."""

import os
from datetime import datetime
from fpdf import FPDF
from src.utils.logger import get_logger

logger = get_logger("veta.reports.pdf")


class VetaPDF(FPDF):
    """PDF personalizado con header y footer de Veta."""

    def __init__(self, client_name: str):
        super().__init__()
        self.client_name = client_name

    def header(self):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Veta Strategist Report — {self.client_name}", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Veta Strategist AI | Page {self.page_no()}/{{nb}}", align="C")


class PDFReportGenerator:

    def generate(self, report_data: dict, output_path: str):
        """Genera un reporte PDF a partir de los datos del análisis."""
        client_name = report_data.get("client_name", "Unknown")
        timestamp = report_data.get("timestamp", datetime.now().strftime("%Y%m%d_%H%M%S"))
        synthesis = report_data.get("synthesis", {})
        agent_results = report_data.get("agent_results", {})

        pdf = VetaPDF(client_name)
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Fecha
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, f"Date: {self._format_timestamp(timestamp)}", ln=True)
        pdf.ln(5)

        # Executive Summary
        exec_summary = synthesis.get("executive_summary", "")
        if exec_summary:
            self._add_section_title(pdf, "Executive Summary")
            self._add_text(pdf, exec_summary)
            pdf.ln(5)

        # Key Insights
        insights = synthesis.get("key_insights", [])
        if insights:
            self._add_section_title(pdf, "Key Insights")
            for insight in insights:
                if isinstance(insight, dict):
                    impact = insight.get("impact", "medium")
                    icon = "[HIGH]" if impact == "high" else "[MED]" if impact == "medium" else "[LOW]"
                    self._add_bullet(pdf, f"{icon} {insight.get('insight', '')}")
                else:
                    self._add_bullet(pdf, str(insight))
            pdf.ln(5)

        # Risk Alerts
        risk_alerts = synthesis.get("risk_alerts", [])
        if risk_alerts:
            self._add_section_title(pdf, "Risk Alerts")
            for alert in risk_alerts:
                if isinstance(alert, dict):
                    urgency = alert.get("urgency", "medium").upper()
                    self._add_subsection(pdf, f"[{urgency}] {alert.get('risk', '')}")
                    if alert.get("action"):
                        self._add_text(pdf, f"Action: {alert['action']}")
                else:
                    self._add_bullet(pdf, str(alert))
            pdf.ln(5)

        # Strategic Recommendations
        recommendations = synthesis.get("strategic_recommendations", [])
        if recommendations:
            self._add_section_title(pdf, "Strategic Recommendations")
            for rec in recommendations:
                if isinstance(rec, dict):
                    priority = rec.get("priority", "")
                    self._add_subsection(pdf, f"{priority}. {rec.get('recommendation', '')}")
                    if rec.get("expected_impact"):
                        self._add_text(pdf, f"Expected Impact: {rec['expected_impact']}")
                    if rec.get("effort"):
                        self._add_text(pdf, f"Effort: {rec['effort']}")
                else:
                    self._add_bullet(pdf, str(rec))
            pdf.ln(5)

        # Action Plan
        action_plan = synthesis.get("action_plan", {})
        if action_plan:
            self._add_section_title(pdf, "Action Plan")
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
                    self._add_subsection(pdf, label)
                    for task in tasks:
                        self._add_bullet(pdf, str(task))

        # Guardar
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pdf.output(output_path)
        logger.info(f"Reporte PDF generado: {output_path}")

    def _add_section_title(self, pdf: FPDF, title: str):
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_draw_color(41, 128, 185)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

    def _add_subsection(self, pdf: FPDF, title: str):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, title, ln=True)

    def _add_text(self, pdf: FPDF, text: str):
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, text)

    def _add_bullet(self, pdf: FPDF, text: str):
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(5)
        pdf.multi_cell(0, 6, f"  - {text}")

    def _format_timestamp(self, timestamp: str) -> str:
        try:
            dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            return timestamp
