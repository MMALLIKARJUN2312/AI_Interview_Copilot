"""Centralized prompt templates for the AI platform
Every AI capability should generate prompts through this module
"""

class PromptMessage:
    """Builds prompts for different AI capabilities"""
    
    @staticmethod
    def build_resume_analysis_prompt(resume_text : str) -> str:
        return f"""
You are an expert Technical Recruiter, Hiring Manager and ATS Specialist.

Analyze the following:

Return only valid JSON

Do Not include markdown.
Do Not include explanations.
Do Not wrap the response inside ```json.

Resume:

{resume_text}

Expected JSON format:

{{
    "ats_score" : 0,
    "strengths" : [],
    "weaknesses" : [],
    "suggestions" : []
}}
    """