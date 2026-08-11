from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import InterviewAnswer
from app.repositories.base_repository import BaseRepository

class InterviewAnswerRepository(BaseRepository[InterviewAnswer]):
    """Repository responsible for InterviewAnswer persistence"""

    def __init__(self) -> None:
        super().__init__(InterviewAnswer)

    def create_answer(self, db : Session, answer : InterviewAnswer) -> InterviewAnswer:
        return self.create(db, answer)

    def get_by_question(self, db : Session, question_id : int) -> InterviewAnswer | None:
        stmt = select(InterviewAnswer).where(InterviewAnswer.question_id == question_id)
        return db.execute(stmt).scalar_one_or_none()
