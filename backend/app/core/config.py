"""FraudDNA Core Settings Configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "FraudDNA"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    DATABASE_URL: str = (
        "postgresql+asyncpg://frauddna_user:frauddna_password@localhost:5432/frauddna_db"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql://frauddna_user:frauddna_password@localhost:5432/frauddna_db"
    )


settings = Settings()
