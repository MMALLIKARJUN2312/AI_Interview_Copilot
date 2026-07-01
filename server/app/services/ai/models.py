from pydantic import BaseModel, Field

class AIResponse(BaseModel):
    """Standard response returned by every AI provider"""
    
    content : str = Field(description="Raw AI response")
    model : str = Field(description="Model used")
    provider : str = Field(description="AI provider")
    prompt_tokens : int | None = None
    completion_tokens : int | None = None
    total_tokens : int | None = None 