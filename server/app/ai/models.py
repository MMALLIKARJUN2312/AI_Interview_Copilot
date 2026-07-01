from pydantic import BaseModel, Field

class ResumeAnalysisResult(BaseModel):
    """Standardized AI response for resume analysis"""
    
    ats_score : int = Field(
        ge=0,
        le=100,
        description="ATS score between 0 and 100"
    )
    strengths : list[str]
    weaknesses : list[str]
    suggestions : list[str]