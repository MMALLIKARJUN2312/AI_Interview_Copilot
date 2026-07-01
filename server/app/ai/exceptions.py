"""Custom Exceptions for the AI platform.
Every exception raised inside the AI subsystem must inherit from AI Exception"""

class AIException(Exception):
    """Base exception for the AI platform"""
    pass 

class AIProviderError(Exception):
    """Raised when communication with the configured AI provider fails"""
    pass

class PromptGenerationError(AIException):
    """Raised when prompt generation fails"""
    pass

class AIResponseParsingError(AIException):
    """Raised when a LLM response cannot be parsed into structured data"""    
    pass

class AIResponseValidationError(AIException):
    """Raised when parsed AI output does not satisfy the required schema"""
    pass

class UnsupportedModelError(AIException):
    """Raised when requesting an unsupported AI model"""
    pass