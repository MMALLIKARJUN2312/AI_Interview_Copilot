from pydantic import BaseModel

class ResumeAnalysisResponse(BaseModel):
    resume_id : int
    analysis_id : int
    target_role : str
    ats_score : int
    strengths : list[str]
    weaknesses : list[str]
    suggestions : list[str]
