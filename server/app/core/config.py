from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal["development", "test", "production"] = "development"

    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    REFRESH_COOKIE_NAME: str = "aic_refresh_token"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    REFRESH_COOKIE_DOMAIN: str | None = None

    CSRF_COOKIE_NAME: str = "aic_csrf_token"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"

    CORS_ORIGINS: str = "http://localhost:3000"

    RATE_LIMIT_ENABLED: bool = True

    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_DIR: str = "uploads/resumes"
    S3_BUCKET_NAME: str | None = None
    AWS_REGION: str | None = None

    # Self-host Piston for production traffic and point this URL at it.
    CODE_EXECUTION_API_URL: str = "http://localhost:2000/api/v2"
    CODE_EXECUTION_TIMEOUT_SECONDS: int = 15

    # Comma-separated providers, tried in order until one succeeds.
    AI_PROVIDER_CHAIN: str = "gemini"

    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @field_validator("REFRESH_COOKIE_DOMAIN", mode="before")
    @classmethod
    def empty_cookie_domain_as_none(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str) and not value.strip():
            return None

        return value

    @model_validator(mode="after")
    def validate_cookie_security(self) -> "Settings":
        if (
            self.REFRESH_COOKIE_SAMESITE == "none"
            and not self.REFRESH_COOKIE_SECURE
        ):
            raise ValueError(
                "REFRESH_COOKIE_SECURE must be true when "
                "REFRESH_COOKIE_SAMESITE is 'none'"
            )

        if (
            self.ENVIRONMENT == "production"
            and not self.REFRESH_COOKIE_SECURE
        ):
            raise ValueError(
                "REFRESH_COOKIE_SECURE must be true in production"
            )

        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()