from fastapi import Request
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def account_or_ip_key(request: Request) -> str:
    """
    Use the authenticated account ID for account quotas.

    Invalid, missing, or non-access tokens fall back to the client IP.
    Authentication dependencies still decide whether the request itself
    is authorized.
    """

    authorization = request.headers.get(
        "Authorization",
        "",
    )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() == "bearer" and token:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[
                    settings.JWT_ALGORITHM,
                ],
            )

            subject = payload.get("sub")
            token_type = payload.get("type")

            if (
                token_type == "access"
                and isinstance(subject, str)
                and subject.isdigit()
                and int(subject) > 0
            ):
                return f"account:{subject}"
        except JWTError:
            pass

    client_address = (
        get_remote_address(request)
        or "unknown"
    )

    return f"ip:{client_address}"


limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.RATE_LIMIT_ENABLED,
    storage_uri=settings.RATE_LIMIT_STORAGE_URI,
    key_prefix=settings.RATE_LIMIT_KEY_PREFIX,
)