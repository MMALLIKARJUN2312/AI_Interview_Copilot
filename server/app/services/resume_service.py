from pypdf import PdfReader
from app.ai.orchestrator import AIOrchestrator
from app.ai.models import ResumeAnalysisResult

class ResumeService:
    
    def __init__(self) -> None:
        self.ai = AIOrchestrator()
    
    @staticmethod
    def extract_text(file_path : str) -> str:
        reader = PdfReader(file_path)
        
        text = ""
        
        for page in reader.pages:
            page_text = page.extract_text()
            
            if page_text:
                text += page_text + "\n"
        
        if not text.strip():
            raise ValueError(
                "Unable to extract the text from the uploaded pdf"
            )
        
        return text 
    
    def analyze_resume(self, resume_text : str) -> ResumeAnalysisResult:
        return self.ai.analyze_resume(resume_text)