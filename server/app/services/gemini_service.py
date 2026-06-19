from google import genai
from app.core.config import Settings

class GeminiService:
    
    @staticmethod
    def analyze_resume(resume_text : str):
        client = genai.Client(api_key=Settings.GEMINI_API_KEY)
        
        prompt = f"""
You are a senior technical recruiter.

Analyze the following resume.

Return Strict JSON.

Resume : 

{resume_text}

Required format:

{{
    "ats_score" : 0-100,
    "strengths" : [],
    "weaknesses" : [],
    "suggestions" : []
}}
"""

        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text