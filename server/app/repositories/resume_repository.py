from sqlalchemy.orm import Session

from app.models.resume import Resume, ResumeStatus

from app.repositories.base_repository import BaseRepository

from sqlalchemy import or_
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
    
    def update_status(self, resume : Resume, status : ResumeStatus) -> Resume:
        resume.status = status
        return resume
    
    def mark_uploaded(self, resume : Resume) -> Resume:
        return self.update_status(resume, ResumeStatus.UPLOADED)
        
    def mark_analyzed(self, resume : Resume) -> Resume:
        return self.update_status(resume, ResumeStatus.ANALYZED)
        
    def mark_failed(self, resume : Resume) -> Resume:
        return self.update_status(resume, ResumeStatus.FAILED)