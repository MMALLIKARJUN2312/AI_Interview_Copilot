from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL : str
    JWT_SECRET : str
    GEMINI_API_KEY : str
    JWT_ALGORITHM : str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 30
    REFRESH_TOKEN_EXPIRE_DAYS : int = 30
    CORS_ORIGINS : str = "http://localhost:3000"

    RATE_LIMIT_ENABLED : bool = True

    STORAGE_BACKEND : str = "local"
    LOCAL_STORAGE_DIR : str = "uploads/resumes"
    S3_BUCKET_NAME : str | None = None
    AWS_REGION : str | None = None

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()