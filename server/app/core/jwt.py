from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from jose import jwt

from app.core.config import settings


def create_access_token(data: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = data.copy()
    payload.update(
        {
            "type": "access",
            "iat": now,
            "exp": expires_at,
            "jti": str(uuid4()),
        }
    )

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )