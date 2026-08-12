from io import BytesIO

from pypdf import PdfReader
from app.ai.orchestrator import AIOrchestrator
from app.ai.models import AIGenerationResult, ResumeAnalysisResult

class ResumeService:

    def __init__(self) -> None:
        self.ai = AIOrchestrator()

    @staticmethod
    def extract_text(file_bytes : bytes) -> str:
        reader = PdfReader(BytesIO(file_bytes))

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

    def analyze_resume(
        self,
        resume_text : str,
        target_role : str,
        job_description : str | None = None,
    ) -> AIGenerationResult[ResumeAnalysisResult]:
        return self.ai.analyze_resume(resume_text, target_role, job_description)
