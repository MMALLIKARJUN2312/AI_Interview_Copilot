from datetime import datetime

from pydantic import BaseModel, Field, field_validator

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
    
class ResumeDetail(ResumeSummary):
    job_description: str | None


class ResumeReanalyzeRequest(BaseModel):
    target_role: str = Field(
        min_length=2,
        max_length=150,
    )
    job_description: str | None = Field(
        default=None,
        max_length=10_000,
    )

    @field_validator("target_role")
    @classmethod
    def normalize_target_role(
        cls,
        value: str,
    ) -> str:
        normalized_value = value.strip()

        if len(normalized_value) < 2:
            raise ValueError(
                "target_role must contain at least 2 characters"
            )

        return normalized_value

    @field_validator("job_description")
    @classmethod
    def normalize_job_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip() or None

class ResumeStatisticsResponse(BaseModel):
    total_resumes: int
    analyzed_resumes: int
    uploaded_resumes: int
    failed_resumes: int
    average_ats_score: float | None