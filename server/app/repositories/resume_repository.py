from sqlalchemy.orm import Session

from app.models.resume import Resume, ResumeStatus
from app.models.resume_analysis import (
    AnalysisStatus,
    ResumeAnalysis,
)

from app.repositories.base_repository import BaseRepository

from sqlalchemy import case, func, or_

class ResumeRepository(BaseRepository[Resume]):
    """Repository responsible for all resume persistence.
    Contains business specific queries that should not exist inside services
    """
    
    def __init__(self) -> None:
        super().__init__(Resume)
        
    def create_resume(self, db : Session, resume : Resume) -> Resume:
        return self.create(db, resume)
    
    def get_by_stored_filename(self, db : Session, stored_filename : str) -> Resume | None:
        return (db.query(Resume).filter(Resume.stored_filename == stored_filename).first())
    
    def get_user_resumes(
        self,
        db: Session,
        user_id: int,
        limit: int,
        offset: int,
        resume_status: ResumeStatus | None = None,
        search_query: str | None = None,
        sort_order: str = "newest",
    ) -> list[Resume]:
        query = db.query(Resume).filter(
            Resume.user_id == user_id
        )
        if resume_status is not None:
            query = query.filter(
                Resume.status == resume_status
            )

        if search_query:
            escaped_query = (
                search_query.strip()
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )

            if escaped_query:
                search_pattern = f"%{escaped_query}%"

                query = query.filter(
                    or_(
                        Resume.target_role.ilike(
                            search_pattern,
                            escape="\\",
                        ),
                        Resume.original_filename.ilike(
                            search_pattern,
                            escape="\\",
                        ),
                    )
                )

        if sort_order == "oldest":
            ordering = (
                Resume.created_at.asc(),
                Resume.id.asc(),
            )
        else:
            ordering = (
                Resume.created_at.desc(),
                Resume.id.desc(),
            )

        return (
            query
            .order_by(*ordering)
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def get_latest_resume(self, db : Session, user_id : int) -> Resume | None:
        return (db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.created_at.desc()).first())
        
    def get_user_resume_count(self, db : Session, user_id : int) -> int:
        return (db.query(Resume).filter(Resume.user_id == user_id).count())
    
    def get_user_resume_statistics(
        self,
        db: Session,
        user_id: int,
    ) -> dict[str, int | float | None]:
        counts = (
            db.query(
                func.count(Resume.id).label(
                    "total_resumes",
                ),
                func.sum(
                    case(
                        (
                            Resume.status
                            == ResumeStatus.ANALYZED,
                            1,
                        ),
                        else_=0,
                    )
                ).label("analyzed_resumes"),
                func.sum(
                    case(
                        (
                            Resume.status
                            == ResumeStatus.UPLOADED,
                            1,
                        ),
                        else_=0,
                    )
                ).label("uploaded_resumes"),
                func.sum(
                    case(
                        (
                            Resume.status
                            == ResumeStatus.FAILED,
                            1,
                        ),
                        else_=0,
                    )
                ).label("failed_resumes"),
            )
            .filter(Resume.user_id == user_id)
            .one()
        )

        average_ats_score = (
            db.query(
                func.avg(
                    ResumeAnalysis.ats_score,
                )
            )
            .join(
                Resume,
                Resume.id == ResumeAnalysis.resume_id,
            )
            .filter(
                Resume.user_id == user_id,
                Resume.status == ResumeStatus.ANALYZED,
                ResumeAnalysis.status
                == AnalysisStatus.SUCCESS,
            )
            .scalar()
        )

        return {
            "total_resumes": counts.total_resumes,
            "analyzed_resumes": (
                counts.analyzed_resumes or 0
            ),
            "uploaded_resumes": (
                counts.uploaded_resumes or 0
            ),
            "failed_resumes": (
                counts.failed_resumes or 0
            ),
            "average_ats_score": (
                float(average_ats_score)
                if average_ats_score is not None
                else None
            ),
        }
    
    def update_status(self, resume : Resume, status : ResumeStatus) -> Resume:
        resume.status = status
        return resume
    
    def mark_uploaded(self, resume : Resume) -> Resume:
        return self.update_status(resume, ResumeStatus.UPLOADED)
        
    def mark_analyzed(self, resume : Resume) -> Resume:
        return self.update_status(resume, ResumeStatus.ANALYZED)
        
    def mark_failed(self, resume : Resume) -> Resume:
        return self.update_status(resume, ResumeStatus.FAILED)