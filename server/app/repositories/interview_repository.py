from sqlalchemy import case, func, select
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
    
    def get_user_sessions_page(
        self,
        db: Session,
        user_id: int,
        limit: int,
        offset: int,
        session_status: InterviewSessionStatus | None = None,
    ) -> list[InterviewSession]:
        statement = select(InterviewSession).where(
            InterviewSession.user_id == user_id
        )

        if session_status is not None:
            statement = statement.where(
                InterviewSession.status == session_status
            )

        statement = (
            statement
            .order_by(
                InterviewSession.created_at.desc(),
                InterviewSession.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(
            db.execute(statement).scalars().all()
        )
        
    def get_user_statistics(
        self,
        db: Session,
        user_id: int,
    ) -> dict[str, int | float | None]:
        statement = select(
            func.count(InterviewSession.id).label(
                "total_sessions"
            ),
            func.sum(
                case(
                    (
                        InterviewSession.status
                        == InterviewSessionStatus.IN_PROGRESS,
                        1,
                    ),
                    else_=0,
                )
            ).label("in_progress_sessions"),
            func.sum(
                case(
                    (
                        InterviewSession.status
                        == InterviewSessionStatus.COMPLETED,
                        1,
                    ),
                    else_=0,
                )
            ).label("completed_sessions"),
            func.avg(
                case(
                    (
                        InterviewSession.status
                        == InterviewSessionStatus.COMPLETED,
                        InterviewSession.overall_score,
                    ),
                    else_=None,
                )
            ).label("average_score"),
        ).where(
            InterviewSession.user_id == user_id
        )

        result = db.execute(statement).one()

        average_score = (
            round(float(result.average_score), 1)
            if result.average_score is not None
            else None
        )

        return {
            "total_sessions": int(
                result.total_sessions or 0
            ),
            "in_progress_sessions": int(
                result.in_progress_sessions or 0
            ),
            "completed_sessions": int(
                result.completed_sessions or 0
            ),
            "average_score": average_score,
        }

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
