from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import InterviewFeedback
from app.repositories.base_repository import BaseRepository

class InterviewFeedbackRepository(BaseRepository[InterviewFeedback]):
    """Repository responsible for InterviewFeedback persistence"""

    def __init__(self) -> None:
        super().__init__(InterviewFeedback)

    def create_feedback(self, db : Session, feedback : InterviewFeedback) -> InterviewFeedback:
        return self.create(db, feedback)

    def get_by_session(self, db : Session, session_id : int) -> InterviewFeedback | None:
        stmt = select(InterviewFeedback).where(InterviewFeedback.session_id == session_id)
        return db.execute(stmt).scalar_one_or_none()
