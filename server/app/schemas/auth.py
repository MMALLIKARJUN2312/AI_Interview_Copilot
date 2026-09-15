from pydantic import BaseModel, EmailStr, Field, field_validator


MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72


def validate_password(value: str) -> str:
    if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(
            "Password must not exceed 72 bytes"
        )

    return value

class EmailRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()

        return value

class RegisterRequest(EmailRequest):
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)

    _validate_password_bytes = field_validator("password")(
        validate_password
    )

class LoginRequest(EmailRequest):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    
    model_config = {"from_attributes": True}