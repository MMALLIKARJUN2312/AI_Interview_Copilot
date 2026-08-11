from app.ai.prompts.base import BasePrompt

class ResumeAnalysisPrompt(BasePrompt):
    """Prompt builder for resume analysis"""

    def build(self, *, resume_text : str, target_role : str, job_description : str | None = None) -> str:
        job_description_section = (
            f"\nTarget Job Description :\n\n{job_description}\n"
            if job_description
            else ""
        )

        return f"""
You are an expert ATS Reviewer,
Technical Recruiter,
and Hiring Manager specifically for the role of "{target_role}".

Analyze the following resume strictly against what a "{target_role}" hiring pipeline
expects: required skills, relevant experience, keyword/ATS match, and seniority signals
for that specific role. Do not give generic feedback that ignores the target role.
{job_description_section}
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
