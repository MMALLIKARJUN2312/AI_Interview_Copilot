from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import LearningRoadmap
from app.repositories.base_repository import BaseRepository

class LearningRoadmapRepository(BaseRepository[LearningRoadmap]):
    """Repository responsible for LearningRoadmap persistence"""

    def __init__(self) -> None:
        super().__init__(LearningRoadmap)

    def create_roadmap(self, db : Session, roadmap : LearningRoadmap) -> LearningRoadmap:
        return self.create(db, roadmap)

    def get_by_session(self, db : Session, session_id : int) -> LearningRoadmap | None:
        stmt = select(LearningRoadmap).where(LearningRoadmap.session_id == session_id)
        return db.execute(stmt).scalar_one_or_none()
