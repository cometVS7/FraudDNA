"""FraudDNA Core Settings Configuration."""

import sys
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def ensure_ml_on_sys_path() -> None:
    """Ensure repository root containing the 'ml' module is on sys.path for joblib unpickling."""
    config_file = Path(__file__).resolve()
    for candidate in [
        config_file.parent.parent.parent.parent,
        config_file.parent.parent.parent,
        Path.cwd(),
        Path.cwd().parent,
    ]:
        if (candidate / "ml").is_dir() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
            break


# Ensure sys.path is configured immediately on import
ensure_ml_on_sys_path()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application Settings
    APP_NAME: str = "FraudDNA"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # "console" for human-readable dev, "json" for production
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # V2 Engineering Feature Flags (Conservative defaults: preserve V1 behavior)
    ENABLE_PERSISTENT_STORAGE: bool = False
    V2_FEATURES_ENABLED: bool = False

    # Security & Request Correlation
    REQUEST_ID_HEADER: str = "X-Request-ID"
    CORRELATION_ID_HEADER: str = "X-Correlation-ID"
    SECRET_KEY: str = "insecure-dev-secret-key-change-in-production"

    # CORS Settings
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://fraud-dna.vercel.app",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        """Parse and normalize CORS origins from various formats (JSON, comma-separated, list)."""
        origins: list[str] = []
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    import json

                    parsed = json.loads(v_trimmed)
                    if isinstance(parsed, list):
                        origins = [
                            str(item).strip().rstrip("/") for item in parsed if str(item).strip()
                        ]
                    else:
                        origins = [str(parsed).strip().rstrip("/")]
                except Exception:
                    origins = [
                        item.strip().rstrip("/")
                        for item in v_trimmed.strip("[]").split(",")
                        if item.strip()
                    ]
            else:
                origins = [
                    item.strip().rstrip("/") for item in v_trimmed.split(",") if item.strip()
                ]
        elif isinstance(v, list | tuple | set):
            origins = [str(item).strip().rstrip("/") for item in v if str(item).strip()]

        default_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://fraud-dna.vercel.app",
        ]
        for default in default_origins:
            if default not in origins:
                origins.append(default)

        return origins

    # Database Configuration (PostgreSQL + pgvector)
    DATABASE_URL: str = (
        "postgresql+asyncpg://frauddna_user:frauddna_password@localhost:5432/frauddna_db"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql://frauddna_user:frauddna_password@localhost:5432/frauddna_db"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: float = 30.0

    # ML & Feature Pipeline Settings
    ML_MODELS_DIR: str = "ml/models"
    ML_DATA_PATH: str = "ml/data/transactions.csv"
    ML_FEATURE_COUNT: int = 18
    ML_DEFAULT_THRESHOLD: float = 0.37

    # Agent Settings
    LLM_PROVIDER: str = "deterministic"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_API_KEY: str | None = None
    LLM_API_BASE: str = "https://api.openai.com/v1"
    AGENT_MAX_STEPS: int = 8
    AGENT_TIMEOUT_SECONDS: float = 30.0

    # Policy Engine Settings
    POLICY_VERSION: str = "2025.1"


settings = Settings()
