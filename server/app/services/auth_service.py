from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.core.security import hash_password

class AuthService:
    
    @staticmethod
    def register_user(db : Session, full_name : str, email : str, password : str):
        existing_user = UserService.get_user_by_email(db, email)
        
        if existing_user:
            raise ValueError("User already exists")
        
        hashed = hash_password(password)
        
        return UserService.create_user(db, full_name, email, hashed)