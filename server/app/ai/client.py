from google import genai
from typing import Type
from pydantic import BaseModel
from app.ai.provider import AIProvider
from app.ai.parser import AIResponseParser
from app.ai.validator import AIResponseValidator
from app.ai.constants import DEFAULT_MODEL
from app.ai.exceptions import AIProviderError
from app.core.config import settings

class GeminiProvider(AIProvider):
    """Gemini implementation of the AIProvider interface"""
    
    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )
        
    def generate(self, prompt : str) -> str:
        try:
            response = self.client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt
            )
            
            if response.text is None:
                raise AIProviderError("Gemini returned an empty response")
            
            return response.text
        
        except Exception as exc:
            raise AIProviderError(f"Gemini request failed : {exc}") from exc
        
class AIClient:
    """Entry point for all AI requests"""
    
    def __init__(self, provider : AIProvider) -> None:
        self.provider = provider
    
    def generate(self, prompt : str) -> str:
        return self.provider.generate(prompt)
    
    def generate_structured(self, *, prompt : str, response_model : Type[BaseModel]) -> BaseModel:
        raw_response = self.generate(prompt)
        parsed = AIResponseParser.parse_json(raw_response)
        
        return AIResponseValidator.validate(response=parsed, response_model=response_model)