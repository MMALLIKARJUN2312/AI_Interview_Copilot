from datetime import datetime

from sqlalchemy import Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.mixins import (PrimaryKeyMixin, TimestampMixin)

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.resume import Resume

class InterviewSessionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class RoundType(str, Enum):
    """Which kind of interview round a question belongs to, mirroring the
    distinct stages of a real interview loop.
    """
    DSA_CODING = "dsa_coding"
    MACHINE_CODING = "machine_coding"
    GENERAL = "general"

class InterviewSession(PrimaryKeyMixin, TimestampMixin, Base):
    """A single role-aligned mock interview attempt tied to one resume."""

    __tablename__ = "interview_sessions"

    user_id : Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id : Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role : Mapped[str] = mapped_column(String(150), nullable=False)
    status : Mapped[InterviewSessionStatus] = mapped_column(
        SQLEnum(InterviewSessionStatus, name="interview_session_status"),
        default=InterviewSessionStatus.PENDING,
        nullable=False,
    )
    total_questions : Mapped[int] = mapped_column(Integer, nullable=False)
    current_index : Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overall_score : Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider : Mapped[str | None] = mapped_column(String(50), nullable=True)
    model : Mapped[str | None] = mapped_column(String(100), nullable=True)
    completed_at : Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user : Mapped["User"] = relationship(back_populates="interview_sessions")
    resume : Mapped["Resume"] = relationship(back_populates="interview_sessions")
    questions : Mapped[list["InterviewQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.order_index"
    )
    feedback : Mapped["InterviewFeedback | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )
    roadmap : Mapped["LearningRoadmap | None"] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )

class InterviewQuestion(PrimaryKeyMixin, TimestampMixin, Base):
    """A single AI-generated question belonging to an interview session."""

    __tablename__ = "interview_questions"

    session_id : Mapped[int] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index : Mapped[int] = mapped_column(Integer, nullable=False)
    question_text : Mapped[str] = mapped_column(Text, nullable=False)
    category : Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty : Mapped[str] = mapped_column(String(20), nullable=False)
    round_type : Mapped[RoundType] = mapped_column(
        SQLEnum(RoundType, name="interview_round_type"),
        default=RoundType.GENERAL,
        nullable=False,
    )
    # Coding-round-only fields (dsa_coding / machine_coding); unused (null) for general questions.
    language : Mapped[str | None] = mapped_column(String(20), nullable=True)
    starter_code : Mapped[str | None] = mapped_column(Text, nullable=True)
    examples : Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints : Mapped[str | None] = mapped_column(Text, nullable=True)
    test_cases : Mapped[list | None] = mapped_column(JSON, nullable=True)

    session : Mapped["InterviewSession"] = relationship(back_populates="questions")
    answer : Mapped["InterviewAnswer | None"] = relationship(
        back_populates="question", cascade="all, delete-orphan", uselist=False
    )

class InterviewAnswer(PrimaryKeyMixin, TimestampMixin, Base):
    """The candidate's answer to a question, plus AI evaluation."""

    __tablename__ = "interview_answers"

    question_id : Mapped[int] = mapped_column(
        ForeignKey("interview_questions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    answer_text : Mapped[str] = mapped_column(Text, nullable=False)
    score : Mapped[int] = mapped_column(Integer, nullable=False)
    feedback : Mapped[str] = mapped_column(Text, nullable=False)
    strengths : Mapped[list] = mapped_column(JSON, nullable=False)
    improvements : Mapped[list] = mapped_column(JSON, nullable=False)
    # Coding-round-only fields; unused (null) for general answers. answer_text
    # holds the submitted source code for coding questions.
    language : Mapped[str | None] = mapped_column(String(20), nullable=True)
    execution_results : Mapped[list | None] = mapped_column(JSON, nullable=True)
    passed_test_count : Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_test_count : Mapped[int | None] = mapped_column(Integer, nullable=True)

    question : Mapped["InterviewQuestion"] = relationship(back_populates="answer")

class InterviewFeedback(PrimaryKeyMixin, TimestampMixin, Base):
    """End-of-session summary feedback for an interview session."""

    __tablename__ = "interview_feedback"

    session_id : Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    overall_score : Mapped[int] = mapped_column(Integer, nullable=False)
    summary : Mapped[str] = mapped_column(Text, nullable=False)
    strengths : Mapped[list] = mapped_column(JSON, nullable=False)
    weaknesses : Mapped[list] = mapped_column(JSON, nullable=False)
    recommendation : Mapped[str] = mapped_column(Text, nullable=False)

    session : Mapped["InterviewSession"] = relationship(back_populates="feedback")

class LearningRoadmap(PrimaryKeyMixin, TimestampMixin, Base):
    """Personalized learning roadmap generated at the end of a session."""

    __tablename__ = "learning_roadmaps"

    session_id : Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    items : Mapped[list] = mapped_column(JSON, nullable=False)

    session : Mapped["InterviewSession"] = relationship(back_populates="roadmap")
