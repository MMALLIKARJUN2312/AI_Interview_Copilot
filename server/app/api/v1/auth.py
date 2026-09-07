from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.core.rbac import require_role
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
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


def resolve_refresh_token(
    request: Request,
    payload: RefreshRequest | LogoutRequest | None,
) -> str | None:
    if payload is not None and payload.refresh_token:
        return payload.refresh_token

    return request.cookies.get(settings.REFRESH_COOKIE_NAME)


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

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
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
    payload: RefreshRequest | None = None,
    db: Session = Depends(get_db),
):
    refresh_token = resolve_refresh_token(request, payload)

    if refresh_token is None:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=401,
            detail="Refresh token is required",
        )

    try:
        access_token, rotated_refresh_token = (
            AuthService.refresh_access_token(db, refresh_token)
        )

        set_refresh_cookie(response, rotated_refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=rotated_refresh_token,
            token_type="bearer",
        )
    except ValueError as error:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=401,
            detail=str(error),
        ) from error


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    payload: LogoutRequest | None = None,
    db: Session = Depends(get_db),
):
    refresh_token = resolve_refresh_token(request, payload)

    if refresh_token is not None:
        AuthService.logout_user(db, refresh_token)

    clear_refresh_cookie(response)

    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return current_user


@router.get("/admin")
def admin_dashboard(
    current_user=Depends(require_role(["admin"])),
):
    return {"message": "Welcome Admin"}