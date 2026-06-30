from pypdf import PdfReader
from app.services.gemini_service import (GeminiService)

class ResumeService:
    
    @staticmethod
    def extract_text(file_path : str):
        reader = PdfReader(file_path)
        
        text = ""
        
        for page in reader.pages:
            page_text = page.extract_text()
            
            if page_text:
                text += page_text + "\n"
        
        return text 
    
    @staticmethod
    def analyze_resume(resume_text : str):
        return (GeminiService.analyze_resume(resume_text))