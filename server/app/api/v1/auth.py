import hmac
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.rbac import require_role
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth",
        domain=settings.REFRESH_COOKIE_DOMAIN,
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path="/auth",
        domain=settings.REFRESH_COOKIE_DOMAIN,
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def create_csrf_token(response: Response) -> str:
    csrf_token = secrets.token_urlsafe(32)

    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
        domain=settings.REFRESH_COOKIE_DOMAIN,
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )

    return csrf_token


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path="/",
        domain=settings.REFRESH_COOKIE_DOMAIN,
        secure=settings.REFRESH_COOKIE_SECURE,
        httponly=True,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def validate_csrf_token(request: Request) -> None:
    cookie_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
    header_token = request.headers.get(settings.CSRF_HEADER_NAME)

    if (
        cookie_token is None
        or header_token is None
        or not hmac.compare_digest(cookie_token, header_token)
    ):
        raise HTTPException(
            status_code=403,
            detail="CSRF validation failed",
        )


@router.get("/csrf")
def csrf(response: Response):
    return {
        "csrf_token": create_csrf_token(response),
    }


@router.post("/register")
@limiter.limit("5/minute")
def register(
    request: Request,
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        user = AuthService.register_user(
            db,
            payload.full_name,
            payload.email,
            payload.password,
        )

        return {
            "message": "User Registered Successfully",
            "user_id": user.id,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        access_token, refresh_token = AuthService.login_user(
            db,
            payload.email,
            payload.password,
        )

        set_refresh_cookie(response, refresh_token)
        create_csrf_token(response)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )
    except ValueError as error:
        raise HTTPException(
            status_code=401,
            detail=str(error),
        ) from error


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get(
        settings.REFRESH_COOKIE_NAME
    )

    if refresh_token is None:
        clear_refresh_cookie(response)
        clear_csrf_cookie(response)

        raise HTTPException(
            status_code=401,
            detail="Refresh token cookie is required",
        )

    validate_csrf_token(request)

    try:
        access_token, rotated_refresh_token = (
            AuthService.refresh_access_token(
                db,
                refresh_token,
            )
        )

        set_refresh_cookie(response, rotated_refresh_token)
        csrf_token = create_csrf_token(response)

        response.headers[
            settings.CSRF_HEADER_NAME
        ] = csrf_token

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )
    except ValueError as error:
        clear_refresh_cookie(response)
        clear_csrf_cookie(response)

        raise HTTPException(
            status_code=401,
            detail=str(error),
        ) from error

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    refresh_token = request.cookies.get(
        settings.REFRESH_COOKIE_NAME
    )

    if refresh_token is not None:
        validate_csrf_token(request)
        AuthService.logout_user(db, refresh_token)

    clear_refresh_cookie(response)
    clear_csrf_cookie(response)

    return {"message": "Logged out"}

@router.post("/logout-all")
def logout_all(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_csrf_token(request)

    revoked_sessions = AuthService.logout_all_sessions(
        db,
        current_user.id,
    )

    clear_refresh_cookie(response)
    clear_csrf_cookie(response)

    return {
        "message": "Logged out from all sessions",
        "revoked_sessions": revoked_sessions,
    }
    
@router.post("/change-password")
@limiter.limit("5/minute")
def change_password(
    request: Request,
    response: Response,
    payload: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_csrf_token(request)

    try:
        revoked_sessions = AuthService.change_password(
            db,
            current_user,
            payload.current_password,
            payload.new_password,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    clear_refresh_cookie(response)
    clear_csrf_cookie(response)

    return {
        "message": "Password changed successfully",
        "revoked_sessions": revoked_sessions,
    }

@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user


@router.get("/admin")
def admin_dashboard(
    current_user=Depends(require_role(["admin"])),
):
    return {"message": "Welcome Admin"}