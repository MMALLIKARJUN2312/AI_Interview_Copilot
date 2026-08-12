from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jwt import create_access_token
from app.core.security import hash_password, verify_password
from app.core.tokens import generate_refresh_token, hash_refresh_token
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.user_service import UserService

refresh_token_repository = RefreshTokenRepository()

class AuthService:

    @staticmethod
    def register_user(db : Session, full_name : str, email : str, password : str) -> User:
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
    def _issue_access_token(user : User) -> str:
        return create_access_token({
            "sub" : str(user.id),
            "email" : user.email,
            "role" : user.role,
        })

    @staticmethod
    def _issue_refresh_token(db : Session, user : User) -> str:
        raw_token = generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token_repository.create_token(db, RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=expires_at,
        ))

        return raw_token

    @classmethod
    def login_user(cls, db : Session, email : str, password : str) -> tuple[str, str]:
        user = UserService.get_user_by_email(db, email)

        if not user:
            raise ValueError("Invalid Credentials")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid Credentials")

        access_token = cls._issue_access_token(user)
        refresh_token = cls._issue_refresh_token(db, user)
        refresh_token_repository.commit(db)

        return access_token, refresh_token

    @classmethod
    def refresh_access_token(cls, db : Session, raw_refresh_token : str) -> tuple[str, str]:
        token_hash = hash_refresh_token(raw_refresh_token)
        stored = refresh_token_repository.get_by_hash(db, token_hash)

        if stored is None or not RefreshTokenRepository.is_valid(stored):
            raise ValueError("Invalid or expired refresh token")

        user = UserService.get_user_by_id(db, stored.user_id)

        if user is None:
            raise ValueError("Invalid or expired refresh token")

        refresh_token_repository.revoke(stored)

        access_token = cls._issue_access_token(user)
        new_refresh_token = cls._issue_refresh_token(db, user)
        refresh_token_repository.commit(db)

        return access_token, new_refresh_token

    @staticmethod
    def logout_user(db : Session, raw_refresh_token : str) -> None:
        token_hash = hash_refresh_token(raw_refresh_token)
        stored = refresh_token_repository.get_by_hash(db, token_hash)

        if stored is not None:
            refresh_token_repository.revoke(stored)
            refresh_token_repository.commit(db)
