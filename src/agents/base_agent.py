"""Clase base para todos los sub-agentes de Veta Strategist."""

import os
import json
from anthropic import Anthropic
from src.utils.logger import get_logger

logger = get_logger("veta.agents")


class BaseAgent:
    """Clase base que conecta un sub-agente con Claude API usando un skill como system prompt."""

    def __init__(
        self,
        name: str,
        skill_file: str,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 4096,
    ):
        self.name = name
        self.skill_file = skill_file
        self.model = model
        self.max_tokens = max_tokens
        self._client = None
        self._system_prompt = None

    @property
    def client(self) -> Anthropic:
        if self._client is None:
            self._client = Anthropic()
        return self._client

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            skill_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "skills",
                self.skill_file,
            )
            with open(skill_path, "r", encoding="utf-8") as f:
                self._system_prompt = f.read()
        return self._system_prompt

    def build_user_prompt(self, data: dict, client_config: dict) -> str:
        """Construye el prompt de usuario con la data. Override en cada sub-agente."""
        raise NotImplementedError("Cada sub-agente debe implementar build_user_prompt")

    def parse_response(self, response_text: str) -> dict:
        """Parsea la respuesta de Claude a un dict estructurado. Override en cada sub-agente."""
        raise NotImplementedError("Cada sub-agente debe implementar parse_response")

    def run(self, data: dict, client_config: dict) -> dict:
        """Ejecuta el sub-agente: prepara data → llama a Claude → parsea respuesta."""
        logger.info(f"[{self.name}] Iniciando análisis...")

        user_prompt = self.build_user_prompt(data, client_config)

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            response_text = message.content[0].text
            logger.info(f"[{self.name}] Respuesta recibida ({message.usage.input_tokens} in, {message.usage.output_tokens} out)")

            result = self.parse_response(response_text)
            result["_meta"] = {
                "agent": self.name,
                "model": self.model,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            }
            return result

        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}")
            return {
                "error": str(e),
                "findings": [],
                "risk_level": "unknown",
                "recommendations": [],
                "_meta": {"agent": self.name, "model": self.model},
            }

    def _try_parse_json(self, text: str) -> dict | None:
        """Intenta extraer y parsear JSON de la respuesta."""
        # Buscar bloques ```json ... ```
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            json_str = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            json_str = text[start:end].strip()
        else:
            json_str = text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
