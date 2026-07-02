from app.ai.client import AIClient, GeminiProvider
from app.ai.models import ResumeAnalysisResult
from app.ai.prompts.registry import PromptRegistry

class AIOrchestrator:
    """Coordinates end-end to AI workflows
    
    Responsibilities: Build prompts, Invoke AI providers, Parse responses, Validate responses 
    """
    
    def __init__(self) -> None:
        self.client = AIClient(provider=GeminiProvider())
        
    def analyze_resume(self, resume_text : str) -> ResumeAnalysisResult:
        prompt = PromptRegistry.resume_analysis().build(resume_text=resume_text)
               
        return self.client.generate_structured(prompt=prompt, response_model=ResumeAnalysisResult)