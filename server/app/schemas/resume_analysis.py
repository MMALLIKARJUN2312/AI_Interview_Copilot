from pydantic import BaseModel

class ResumeAnalysisResponse(BaseModel):
    ats_score : int
    strengths : list[str]
    weaknesses : list[str]
    suggestions : list[str]
    
    