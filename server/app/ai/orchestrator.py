from app.ai.client import AIClient, GeminiProvider
from app.ai.parser import AIResponseParser
from app.ai.prompts import PromptManager
from app.ai.validator import AIResponseValidator
from app.ai.models import ResumeAnalysisResult

class AIOrchestrator:
    """Coordinates end-end to AI workflows
    
    Responsibilities: Build prompts, Invoke AI providers, Parse responses, Validate responses 
    """
    
    def __init__(self) -> None:
        self.client = AIClient(provider=GeminiProvider())
        
    def analyze_resume(self, resume_text : str) -> ResumeAnalysisResult:
        prompt = PromptManager.build_resume_analysis_prompt(resume_text)
        
        return self.client.generate_structured(prompt=prompt, response_model=ResumeAnalysisResult)