"""Strategic Synthesizer — consolida resultados de todos los sub-agentes."""

import json
from src.agents.base_agent import BaseAgent


class Synthesizer(BaseAgent):

    def __init__(self, model: str = "claude-opus-4-6"):
        super().__init__(
            name="Strategic Synthesizer",
            skill_file="market.md",
            model=model,
            max_tokens=8192,
        )

    def run(self, agent_results: dict, client_config: dict) -> dict:
        """Override de run() porque recibe resultados de agentes, no data cruda."""
        from src.utils.logger import get_logger
        logger = get_logger("veta.synthesizer")
        logger.info("[Strategic Synthesizer] Consolidando resultados...")

        user_prompt = self.build_user_prompt(
            {"analysis_results": agent_results}, client_config
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            response_text = message.content[0].text
            logger.info(
                f"[Strategic Synthesizer] Síntesis completada "
                f"({message.usage.input_tokens} in, {message.usage.output_tokens} out)"
            )

            result = self.parse_response(response_text)
            result["_meta"] = {
                "agent": self.name,
                "model": self.model,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            }
            return result

        except Exception as e:
            logger.error(f"[Strategic Synthesizer] Error: {e}")
            return {"error": str(e), "raw_response": ""}

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        sections = []
        goals = client_config.get("goals", {})

        sections.append(f"# Strategic Synthesis: {client_config.get('client_name', 'Unknown')}")
        sections.append(f"Primary KPI: {goals.get('primary_kpi', 'CPA')}")
        sections.append(f"Target CPA: {goals.get('target_cpa', 'N/A')}")
        sections.append(f"Target ROAS: {goals.get('target_roas', 'N/A')}")
        sections.append(f"Monthly Budget: {goals.get('monthly_budget', 'N/A')} {goals.get('currency', 'USD')}")

        analysis_results = data.get("analysis_results", {})

        for agent_name, result in analysis_results.items():
            sections.append(f"\n## {agent_name.upper()} Agent Results")
            clean_result = {k: v for k, v in result.items() if not k.startswith("_")}
            sections.append(json.dumps(clean_result, indent=2, default=str))

        sections.append(
            "\nSynthesize all findings into a unified strategic report. "
            "Provide your response in the required JSON format with executive summary, "
            "key insights, risk alerts, strategic recommendations, and action plan."
        )
        return "\n".join(sections)

    def parse_response(self, response_text: str) -> dict:
        parsed = self._try_parse_json(response_text)
        if parsed:
            return parsed

        return {
            "executive_summary": "",
            "key_insights": [],
            "risk_alerts": [],
            "strategic_recommendations": [],
            "action_plan": {},
            "raw_response": response_text,
        }
