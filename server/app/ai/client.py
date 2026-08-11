import time

from google import genai
from typing import Type
from pydantic import BaseModel
from app.ai.provider import AIProvider
from app.ai.parser import AIResponseParser
from app.ai.validator import AIResponseValidator
from app.ai.constants import DEFAULT_MODEL
from app.ai.exceptions import AIProviderError
from app.ai.models import AIGenerationResult
from app.core.config import settings
from app.core.logger import logger
from app.ai.retry import retry_ai_request

class GeminiProvider(AIProvider):
    """Gemini implementation of the AIProvider interface"""

    name = "gemini"
    model = DEFAULT_MODEL

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    @retry_ai_request    
    def generate(self, prompt : str) -> str:
        try:
            logger.info("Sending request to the Gemini model: %s", DEFAULT_MODEL)
            response = self.client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt
            )
            
            if response.text is None:
                raise AIProviderError("Gemini returned an empty response")
            
            logger.info("Gemini request completed successfully")
            
            return response.text
        
        except Exception as exc:
            logger.exception("Gemini request failed")
            raise AIProviderError("Failed to communicate with the AI provider") from exc
        
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