from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository

class UserService:
    """Application service responsible for user-related business operations"""
    
    repository = UserRepository()
    
    @classmethod
    def get_user_by_email(cls, db : Session, email : str) -> User | None:
        return cls.repository.get_by_email(db, email)
        
    @classmethod
    def create_user(cls, db : Session, full_name : str, email : str, hashed_password : str) -> User:
        user = User(full_name=full_name, email=email, hashed_password=hashed_password)
        cls.repository.create(db, user)
        cls.repository.commit(db)
        cls.repository.refresh(db, user)
        return user
        
    @classmethod
    def get_user_by_id(cls, db : Session, user_id : int) -> User | None:
        return cls.repository.get_by_id(db, user_id)