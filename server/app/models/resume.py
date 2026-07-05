from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.mixins import (PrimaryKeyMixin, TimestampMixin)

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.resume_analysis import ResumeAnalysis

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
    status : Mapped[ResumeStatus] = mapped_column(SQLEnum(ResumeStatus, name = "resume_status"), default=ResumeStatus.UPLOADED, nullable=False)
    user : Mapped["User"] = relationship(back_populates="resumes")
    analyses : Mapped[list["ResumeAnalysis"]] = relationship(back_populates="resume", cascade="all, delete-orphan")