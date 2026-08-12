from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.mixins import (PrimaryKeyMixin, TimestampMixin)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class RefreshToken(PrimaryKeyMixin, TimestampMixin, Base):
    """A rotated, hashed refresh token. The raw token is only ever returned to
    the client once, at issuance; only its SHA-256 hash is persisted.
    """

    __tablename__ = "refresh_tokens"

    user_id : Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash : Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked : Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user : Mapped["User"] = relationship(back_populates="refresh_tokens")
