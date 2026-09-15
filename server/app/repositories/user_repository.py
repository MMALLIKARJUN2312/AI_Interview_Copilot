from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    """Repository is responsible for database operations related to users"""
    def __init__(self) -> None:
        super().__init__(User)
    
    def get_by_email(self, db: Session, email: str) -> User | None:
        normalized_email = email.strip().lower()

        return (db.query(User).filter(func.lower(User.email) == normalized_email).first())
    
    def get_by_role(self, db : Session, role : str) -> list[User]:
        return (db.query(User).filter(User.role == role).all())