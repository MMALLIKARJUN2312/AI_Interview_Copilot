from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.resume_analysis import (ResumeAnalysis, AnalysisStatus)

from app.repositories.base_repository import BaseRepository

class ResumeAnalysisRepository(BaseRepository[ResumeAnalysis]):
    """Repository responsible for ResumeAnalysis persistence"""
    
    def __init__(self):
        super().__init__(ResumeAnalysis)
        
    def create_analysis(self, db : Session, analysis : ResumeAnalysis) -> ResumeAnalysis:
        return self.create(db, analysis)
    
    def get_latest_analysis(self, db : Session, resume_id : int) -> ResumeAnalysis | None:
        stmt = (select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id).order_by(ResumeAnalysis.created_at.desc()).limit(1))

        return db.execute(stmt).scalar_one_or_none()

    def get_analysis_history(self, db : Session, resume_id : int) -> list[ResumeAnalysis]:
        stmt = (select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id).order_by(ResumeAnalysis.created_at.desc()))

        return list(db.execute(stmt).scalars().all())
    
    def get_successful_analyses(self, db : Session, resume_id : int) -> list[ResumeAnalysis]:
        stmt = (select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id, ResumeAnalysis.status == AnalysisStatus.SUCCESS))
        
        return list(db.execute(stmt).scalars().all())

    def get_failed_analyses(self, db : Session, resume_id : int) -> list[ResumeAnalysis]:
        stmt = (select(ResumeAnalysis).where(ResumeAnalysis.resume_id == resume_id, ResumeAnalysis.status == AnalysisStatus.FAILED))
        
        return list(db.execute(stmt).scalars().all())
    
    def count_resume_analyses(self, db : Session, resume_id : int) -> int:
        stmt = (select(func.count(ResumeAnalysis.id)).where(ResumeAnalysis.resume_id == resume_id))
        
        return db.execute(stmt).scalar_one()
        
    def average_ats_score(self, db : Session, resume_id : int) -> float:
        stmt = (select(func.avg(ResumeAnalysis.ats_score)).where(ResumeAnalysis.resume_id == resume_id))
        result =  db.execute(stmt).scalar_one()     
        
        return float(result or 0)
        
    def provider_statistics(self, db : Session):
        stmt = (select(ResumeAnalysis.provider, func.count(ResumeAnalysis.id)).group_by(ResumeAnalysis.provider))
        
        return db.execute(stmt).all()