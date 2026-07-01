from enum import Enum

class AIProvider(str, Enum):
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    
class PromptType(str, Enum):
    "RESUME_ANALYSIS" = "resume_analysis"
    "MOCK_INTERVIEW" = "mock_interview"
    "JOB_MATCH" = "job_match"
    "COVER_LETTER" = "cover_letter"
    
class AIResponseFormat(str, Enum):
    "JSON" = "json"
    "TEXT" = "text"