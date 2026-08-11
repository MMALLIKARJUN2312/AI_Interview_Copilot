from datetime import datetime

from pydantic import BaseModel

class ResumeUploadResponse(BaseModel):
    resume_id : int
    file_name : str
    target_role : str

class ResumeSummary(BaseModel):
    id : int
    original_filename : str
    target_role : str
    status : str
    created_at : datetime

    model_config = {"from_attributes" : True}
