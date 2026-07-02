"""Validation utilities from AI responses"""

from typing import Type
from pydantic import  BaseModel,ValidationError
from app.ai.exceptions import AIResponseValidationError

class AIResponseValidator:
    """Validates parsed AI responses against Pydantic models"""
    
    @staticmethod
    def validate(response : dict, response_model : Type[BaseModel]) -> BaseModel:
        try:
            return response_model.model_validate(response)
        
        except ValidationError as exc:
            raise AIResponseValidationError("AI response validation failed") from exc