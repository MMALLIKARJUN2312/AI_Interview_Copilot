from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import InterviewSession, InterviewSessionStatus
from app.repositories.base_repository import BaseRepository

class InterviewSessionRepository(BaseRepository[InterviewSession]):
    """Repository responsible for InterviewSession persistence"""

    def __init__(self) -> None:
        super().__init__(InterviewSession)

    def create_session(self, db : Session, session : InterviewSession) -> InterviewSession:
        return self.create(db, session)

    def get_user_sessions(self, db : Session, user_id : int) -> list[InterviewSession]:
        stmt = (
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    def get_resume_sessions(self, db : Session, resume_id : int) -> list[InterviewSession]:
        stmt = (
            select(InterviewSession)
            .where(InterviewSession.resume_id == resume_id)
            .order_by(InterviewSession.created_at.desc())
        )
        return list(db.execute(stmt).scalars().all())

    def mark_in_progress(self, session : InterviewSession) -> InterviewSession:
        session.status = InterviewSessionStatus.IN_PROGRESS
        return session

    def mark_completed(self, session : InterviewSession) -> InterviewSession:
        session.status = InterviewSessionStatus.COMPLETED
        return session

    def mark_abandoned(self, session : InterviewSession) -> InterviewSession:
        session.status = InterviewSessionStatus.ABANDONED
        return session
