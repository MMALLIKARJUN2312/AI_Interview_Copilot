from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import InterviewQuestion, InterviewAnswer
from app.repositories.base_repository import BaseRepository

class InterviewQuestionRepository(BaseRepository[InterviewQuestion]):
    """Repository responsible for InterviewQuestion persistence"""

    def __init__(self) -> None:
        super().__init__(InterviewQuestion)

    def create_questions(self, db : Session, questions : list[InterviewQuestion]) -> list[InterviewQuestion]:
        return self.create_many(db, questions)

    def get_by_session(self, db : Session, session_id : int) -> list[InterviewQuestion]:
        stmt = (
            select(InterviewQuestion)
            .where(InterviewQuestion.session_id == session_id)
            .order_by(InterviewQuestion.order_index)
        )
        return list(db.execute(stmt).scalars().all())

    def get_next_unanswered(self, db : Session, session_id : int) -> InterviewQuestion | None:
        stmt = (
            select(InterviewQuestion)
            .outerjoin(InterviewAnswer, InterviewAnswer.question_id == InterviewQuestion.id)
            .where(InterviewQuestion.session_id == session_id, InterviewAnswer.id.is_(None))
            .order_by(InterviewQuestion.order_index)
            .limit(1)
        )
        return db.execute(stmt).scalar_one_or_none()
