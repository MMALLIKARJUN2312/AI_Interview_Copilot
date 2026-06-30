from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository

class UserService:
    """Application service responsible for user-related business operations"""
    
    @staticmethod
    def get_user_by_email(db : Session, email : str)-> User | None:
        return UserRepository.get_by_email(db, email)
    
    @staticmethod
    def create_user(db : Session, *, full_name : str, email : str, hashed_password : str, role : str = "candidate") -> User:
        return UserRepository.create(db=db, full_name=full_name, email=email, hashed_password=hashed_password, role=role)