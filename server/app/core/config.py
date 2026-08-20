from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL : str
    JWT_SECRET : str
    JWT_ALGORITHM : str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 30
    REFRESH_TOKEN_EXPIRE_DAYS : int = 30
    CORS_ORIGINS : str = "http://localhost:3000"

    RATE_LIMIT_ENABLED : bool = True

    STORAGE_BACKEND : str = "local"
    LOCAL_STORAGE_DIR : str = "uploads/resumes"
    S3_BUCKET_NAME : str | None = None
    AWS_REGION : str | None = None

    # Public Piston instance by default; self-host https://github.com/engineer-man/piston
    # and point this at it for production traffic (the public instance is rate-limited).
    CODE_EXECUTION_API_URL : str = "https://emkc.org/api/v2/piston"
    CODE_EXECUTION_TIMEOUT_SECONDS : int = 15

    # Comma-separated provider keys, tried in order until one succeeds. Built-in:
    # "gemini", "groq", "openrouter". Each provider is only constructed (and its
    # API key required) if it's actually listed here.
    AI_PROVIDER_CHAIN : str = "gemini"

    GEMINI_API_KEY : str | None = None
    GEMINI_MODEL : str = "gemini-3.5-flash-lite"

    # Free tier at https://console.groq.com - fast inference, generous free quota.
    GROQ_API_KEY : str | None = None
    GROQ_MODEL : str = "llama-3.3-70b-versatile"

    # Free-tier models at https://openrouter.ai (look for a ":free" suffix).
    OPENROUTER_API_KEY : str | None = None
    OPENROUTER_MODEL : str = "meta-llama/llama-3.3-70b-instruct:free"

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()