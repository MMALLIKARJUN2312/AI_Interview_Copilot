from app.ai.prompts.resume import ResumeAnalysisPrompt

class PromptRegistry:
    """central registry for all prompt builders"""
    
    @staticmethod
    def resume_analysis() -> ResumeAnalysisPrompt:
        return ResumeAnalysisPrompt() 
    
    