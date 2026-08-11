from enum import Enum

class AIProvider(str, Enum):
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    
class PromptType(str, Enum):
    RESUME_ANALYSIS = "resume_analysis"
    INTERVIEW_QUESTIONS = "interview_questions"
    ANSWER_EVALUATION = "answer_evaluation"
    INTERVIEW_SUMMARY = "interview_summary"
    LEARNING_ROADMAP = "learning_roadmap"
    JOB_MATCH = "job_match"
    COVER_LETTER = "cover_letter"

class AIResponseFormat(str, Enum):
    JSON = "json"
    TEXT = "text"