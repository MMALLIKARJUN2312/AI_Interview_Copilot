from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.repositories.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository responsible for refresh-token persistence."""

    def __init__(self) -> None:
        super().__init__(RefreshToken)

    def create_token(
        self,
        db: Session,
        token: RefreshToken,
    ) -> RefreshToken:
        return self.create(db, token)

    def get_by_hash(
        self,
        db: Session,
        token_hash: str,
    ) -> RefreshToken | None:
        statement = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )

        return db.execute(statement).scalar_one_or_none()

    def consume_valid_token(
        self,
        db: Session,
        token_hash: str,
    ) -> int | None:
        """
        Atomically revoke a valid refresh token and return its user ID.

        The conditional UPDATE ensures that concurrent requests cannot
        successfully consume the same refresh token more than once.
        """
        statement = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at
                > datetime.now(timezone.utc),
            )
            .values(revoked=True)
            .returning(RefreshToken.user_id)
        )

        return db.execute(statement).scalar_one_or_none()

    def revoke(
        self,
        token: RefreshToken,
    ) -> RefreshToken:
        token.revoked = True
        return token

    def revoke_all_for_user(self, db: Session, user_id: int) -> int:
        statement = (
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
            )
            .values(revoked=True)
        )

        result = db.execute(statement)

        return result.rowcount