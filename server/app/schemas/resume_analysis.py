from datetime import datetime
from pydantic import BaseModel

class ResumeAnalysisResponse(BaseModel):
    resume_id : int
    analysis_id : int
    target_role : str
    ats_score : int
    strengths : list[str]
    weaknesses : list[str]
    suggestions : list[str]

class ResumeAnalysisHistoryResponse(BaseModel):
    id: int
    ats_score: int
    status: str
    provider: str
    model: str
    processing_time_ms: int
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}