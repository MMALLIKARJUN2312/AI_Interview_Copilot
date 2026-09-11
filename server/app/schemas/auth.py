from pydantic import BaseModel, EmailStr, Field, field_validator


MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72


def validate_password(value: str) -> str:
    if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(
            "Password must not exceed 72 bytes"
        )

    return value


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)

    _validate_password_bytes = field_validator("password")(
        validate_password
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str

    model_config = {"from_attributes": True}