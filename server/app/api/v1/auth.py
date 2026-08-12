from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    LogoutRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.rbac import require_role

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register")
@limiter.limit("5/minute")
def register(request : Request, payload : RegisterRequest, db : Session = Depends(get_db)):
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

@router.post('/login', response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request : Request, payload : LoginRequest, db : Session = Depends(get_db)):
    try :
        access_token, refresh_token = AuthService.login_user(db, payload.email, payload.password)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))

@router.post('/refresh', response_model=TokenResponse)
@limiter.limit("20/minute")
def refresh(request : Request, payload : RefreshRequest, db : Session = Depends(get_db)):
    try:
        access_token, refresh_token = AuthService.refresh_access_token(db, payload.refresh_token)

        return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))

@router.post('/logout')
def logout(payload : LogoutRequest, db : Session = Depends(get_db)):
    AuthService.logout_user(db, payload.refresh_token)

    return {"message" : "Logged out"}

@router.get('/me', response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user

@router.get('/admin')
def admin_dashboard(current_user=Depends(require_role(["admin"]))):
    return {"message" : "Welcome Admin"}
