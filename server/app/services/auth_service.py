from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token

class AuthService:
    
    @staticmethod
    def register_user(db : Session, full_name : str, email : str, password : str):
        existing_user = UserService.get_user_by_email(db, email)
        
        if existing_user:
            raise ValueError("User already exists")
        
        hashed = hash_password(password)
        
        return UserService.create_user(
            db=db, 
            full_name=full_name,
            email=email, 
            hashed_password=hashed)
    
    @staticmethod
    def login_user(db, email, password):
        user = UserService.get_user_by_email(db, email)
        
        if not user:
            raise ValueError("Invalid Credentials")
        
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid Credentials")
        
        token = create_access_token({
            "sub" : str(user.id),
            "email" : user.email,
            "role" : user.role
        })
        
        return token 