from app.ai.prompts.base import BasePrompt

class ResumeAnalysisPrompt(BasePrompt):
    """Prompt builder for resume analysis"""
    
    def build(self, *, resume_text : str) -> str:
        return f"""
You are an expert ATS Reviewer,
Technical Recruiter,
and Software Engineering Hiring Manager. 

Analyze the following resume.

Return only valid JSON.

Do Not include markdown.

Do Not include explanations.

Resume : 

{resume_text}

Expected format : 

{{
    "ats_score": 0,
    "strengths": [],
    "weaknesses": [],
    "suggestions": []
}}
    """