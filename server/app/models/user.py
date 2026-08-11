from app.db.database import Base
from app.db.mixins import (PrimaryKeyMixin, TimestampMixin)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.interview import InterviewSession
class User(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    full_name : Mapped[str] = mapped_column(nullable=False)
    email : Mapped[str] = mapped_column(unique=True ,nullable=False)
    hashed_password : Mapped[str] = mapped_column(nullable=False)
    role : Mapped[str] = mapped_column(default="candidate")
    resumes : Mapped[list["Resume"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    interview_sessions : Mapped[list["InterviewSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    
    