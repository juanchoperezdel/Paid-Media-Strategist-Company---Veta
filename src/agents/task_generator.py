"""Sub-Agent 6: Operations Task Generator."""

import json
from src.agents.base_agent import BaseAgent


class TaskGenerator(BaseAgent):

    def __init__(self, model: str = "claude-sonnet-4-6"):
        super().__init__(
            name="Operations Task Generator",
            skill_file="market-tasks.md",
            model=model,
        )

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        sections = []
        goals = client_config.get("goals", {})

        sections.append(f"# Task Generation: {client_config.get('client_name', 'Unknown')}")
        sections.append(f"Primary KPI: {goals.get('primary_kpi', 'CPA')}")
        sections.append(f"Monthly Budget: {goals.get('monthly_budget', 'N/A')} {goals.get('currency', 'USD')}")

        # Incluir resultados de los otros agentes
        analysis_results = data.get("analysis_results", {})
        if analysis_results:
            sections.append("\n## Analysis Results from Other Agents")

            for agent_name, result in analysis_results.items():
                sections.append(f"\n### {agent_name.upper()} Agent Findings")
                # Limpiar metadata antes de enviar
                clean_result = {k: v for k, v in result.items() if not k.startswith("_")}
                sections.append(json.dumps(clean_result, indent=2, default=str))
        else:
            sections.append("\nNo analysis results from other agents available.")

        sections.append("\n## IMPORTANT: Human Approval Required")
        sections.append("All tasks are PROPOSALS for human review. No action should be auto-executed.")
        sections.append("For each task, include: what to do, why, expected impact, and who should approve.")
        sections.append("\nGenerate actionable tasks based on all findings in the required JSON format.")
        return "\n".join(sections)

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "tasks": [],
            "summary": {"total_tasks": 0},
            "top_3_immediate_actions": [],
            "raw_response": response_text,
        }
