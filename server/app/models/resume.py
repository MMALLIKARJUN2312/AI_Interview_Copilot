from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.mixins import (PrimaryKeyMixin, TimestampMixin)

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.resume_analysis import ResumeAnalysis
    from app.models.interview import InterviewSession

class ResumeStatus(str, Enum):
    UPLOADED = "uploaded"
    ANALYZED = "analyzed"
    FAILED = "failed"

class Resume(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"
    
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename : Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename : Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    mime_type : Mapped[str] = mapped_column(String(100), nullable=False)
    file_size : Mapped[int] = mapped_column(Integer, nullable=False)
    target_role : Mapped[str] = mapped_column(String(150), nullable=False)
    job_description : Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text : Mapped[str | None] = mapped_column(Text, nullable=True)
    status : Mapped[ResumeStatus] = mapped_column(SQLEnum(ResumeStatus, name = "resume_status"), default=ResumeStatus.UPLOADED, nullable=False)
    user : Mapped["User"] = relationship(back_populates="resumes")
    analyses : Mapped[list["ResumeAnalysis"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    interview_sessions : Mapped[list["InterviewSession"]] = relationship(back_populates="resume", cascade="all, delete-orphan")