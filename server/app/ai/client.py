import time

from typing import Type
from pydantic import BaseModel
from app.ai.provider import AIProvider
from app.ai.parser import AIResponseParser
from app.ai.validator import AIResponseValidator
from app.ai.models import AIGenerationResult

class AIClient:
    """Entry point for all AI requests"""

    def __init__(self, provider : AIProvider) -> None:
        self.provider = provider

    def generate(self, prompt : str) -> str:
        return self.provider.generate(prompt)

    def generate_structured(self, *, prompt : str, response_model : Type[BaseModel]) -> AIGenerationResult:
        start = time.perf_counter()
        raw_response = self.generate(prompt)
        parsed = AIResponseParser.parse_json(raw_response)
        validated = AIResponseValidator.validate(response=parsed, response_model=response_model)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        return AIGenerationResult(
            data=validated,
            provider=self.provider.name,
            model=self.provider.model,
            processing_time_ms=elapsed_ms,
        )
