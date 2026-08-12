from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.repositories.base_repository import BaseRepository

class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository responsible for RefreshToken persistence"""

    def __init__(self) -> None:
        super().__init__(RefreshToken)

    def create_token(self, db : Session, token : RefreshToken) -> RefreshToken:
        return self.create(db, token)

    def get_by_hash(self, db : Session, token_hash : str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return db.execute(stmt).scalar_one_or_none()

    def revoke(self, token : RefreshToken) -> RefreshToken:
        token.revoked = True
        return token

    def revoke_all_for_user(self, db : Session, user_id : int) -> None:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        for token in db.execute(stmt).scalars().all():
            token.revoked = True

    @staticmethod
    def is_valid(token : RefreshToken) -> bool:
        expires_at = token.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return not token.revoked and expires_at > datetime.now(timezone.utc)
