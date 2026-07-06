from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.mixins import (PrimaryKeyMixin, TimestampMixin)

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.resume import Resume
    
class AnalysisStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    
class ResumeAnalysis(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_analyses"
    
    resume_id : Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    ats_score : Mapped[int] = mapped_column(Integer, nullable=False)
    strengths : Mapped[list] = mapped_column(JSON, nullable=False)
    weaknesses : Mapped[list] = mapped_column(JSON, nullable=False)
    suggestions : Mapped[list] = mapped_column(JSON, nullable=False)
    provider : Mapped[str] = mapped_column(String(50), nullable=False)
    model : Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version : Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    analysis_version : Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    processing_time_ms : Mapped[int] = mapped_column(Integer, nullable=False)
    status : Mapped[AnalysisStatus] = mapped_column(SQLEnum(AnalysisStatus, name = "analysis_status"), default=AnalysisStatus.SUCCESS, nullable=False)
    error_message : Mapped[str | None] = mapped_column(String(500), nullable=True)
    resume : Mapped["Resume"] = relationship(back_populates="analyses")