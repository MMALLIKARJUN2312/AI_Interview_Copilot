from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session 
from app.db.session import get_db
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register")
def register(payload : RegisterRequest, db : Session = Depends(get_db)):
    try :
        user = (
            AuthService.register_user(
                db, 
                payload.full_name,
                payload.email,
                payload.password
            )
        )
        
        return {
            "message" : "User Registered Successfully",
            "user_id" : user.id
        }
    except ValueError as error: 
        raise HTTPException(status_code=400, detail=str(error))