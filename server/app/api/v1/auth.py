from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session 
from app.db.session import get_db
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.core.rbac import require_role

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
    
@router.post('/login')
def login(payload : LoginRequest, db : Session = Depends(get_db)):
    try :
        token = AuthService.login_user(db, payload.email, payload.password)
        
        return {"access_token" : token, "token_type" : "bearer"}

    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))
    
@router.get('/me')
def me(current_user=Depends(get_current_user)):
    return current_user

@router.get('/admin')
def admin_dashboard(current_user=Depends(require_role(["admin"]))):
    return {"message" : "Welcome Admin"}