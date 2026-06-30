from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User

class UserRepository:
    """Repository is responsible for database operations related to users"""
    
    @staticmethod
    def get_by_email(db : Session, email : str)-> Optional[User]:
        return (db.query(User).filter(User.email == email).first())
    
    @staticmethod
    def get_by_id(db : Session, user_id : int) -> Optional[User]:
        return (db.query(User).filter(User.id == user_id).first())
    
    @staticmethod
    def create(db : Session, *, full_name : str, email : str, hashed_password : str, role : str = "candidate")-> User:
        user = User(full_name = full_name, email = email, hashed_password = hashed_password, role = role)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user 
    
    @staticmethod
    def update(db : Session, user : User) -> User:
        db.commit()
        db.refresh(user)
        
        return user 
    
    def delete(db : Session, user : User) -> None:
        db.delete(user)
        db.commit()
        