"""Validation utilities from AI responses"""

from pydantic import  ValidationError
from app.ai.exceptions import AIResponseValidationError
from app.ai.models import ResumeAnalysisResult

class AIResponseValidator:
    """Validates parsed AI responses against Pydantic models"""
    
    @staticmethod
    def validate_resume_analysis(response : dict) -> ResumeAnalysisResult:
        try:
            return ResumeAnalysisResult.model_validate(response)
        
        except ValidationError as exc:
            raise AIResponseValidationError("AI response validation failed") from exc