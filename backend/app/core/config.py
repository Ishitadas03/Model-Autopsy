"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Any, List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        # Resolve relative to the backend package, independent of the working directory.
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Model Autopsy API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    PORT: int = Field(default=8000, description="Server listen port (Render environment)")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/model_autopsy",
        description="Async PostgreSQL connection URL",
    )
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )
    CORS_ORIGIN_REGEX: Optional[str] = Field(
        default=r"^https://.*\.vercel\.app$",
        description="Regex pattern for allowed dynamic origins (e.g. Vercel deployments)",
    )

    # Cloudflare R2 Object Storage (S3-compatible)
    R2_ACCOUNT_ID: Optional[str] = Field(default=None, description="Cloudflare Account ID")
    R2_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="R2 Access Key ID")
    R2_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="R2 Secret Access Key")
    R2_BUCKET_NAME: str = Field(default="model-autopsy-artifacts", description="R2 Bucket Name")
    R2_ENDPOINT_URL: Optional[str] = Field(default=None, description="R2 S3 Endpoint URL override")

    # ML Engine paths
    ML_ENGINE_PATH: Path = Field(
        default=Path(__file__).parent.parent.parent.parent / "ml_engine",
        description="Path to ML engine root directory",
    )
    ARTIFACTS_BASE_DIR: Path = Field(
        default=Path(__file__).parent.parent.parent.parent / "artifacts" / "experiments",
        description="Base directory for experiment artifacts",
    )
    CONFIGS_BASE_DIR: Path = Field(
        default=Path(__file__).parent.parent.parent.parent / "configs" / "experiments",
        description="Base directory for experiment YAML configs",
    )
    SCRIPTS_BASE_DIR: Path = Field(
        default=Path(__file__).parent.parent.parent.parent / "scripts" / "experiments",
        description="Base directory for experiment runner scripts",
    )

    # Experiment execution
    MAX_CONCURRENT_EXPERIMENTS: int = 2
    EXPERIMENT_TIMEOUT_SECONDS: int = 3600  # 1 hour default
    DEFAULT_SEEDS: List[int] = Field(
        default=[42, 123, 456, 789, 1011],
        description="Default seeds for multi-seed experiments",
    )

    # Security (optional, for future)
    API_KEY: Optional[str] = None

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        """Parse debug boolean safely."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on", "debug")
        return bool(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list, supporting JSON or comma-separated."""
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    return json.loads(v_str)
                except Exception:
                    pass
            return [origin.strip().strip("'").strip('"') for origin in v_str.split(",")]
        return v

    @field_validator("ML_ENGINE_PATH", "ARTIFACTS_BASE_DIR", "CONFIGS_BASE_DIR", "SCRIPTS_BASE_DIR", mode="before")
    @classmethod
    def resolve_path(cls, v: str | Path) -> Path:
        """Resolve path to absolute."""
        return Path(v).resolve()

    @field_validator("DEFAULT_SEEDS", mode="before")
    @classmethod
    def parse_seeds(cls, v: str | List[int]) -> List[int]:
        """Parse seeds from string or list."""
        if isinstance(v, str):
            return [int(s.strip()) for s in v.split(",")]
        return v

    @property
    def database_url_sync(self) -> str:
        """Get sync database URL for Alembic."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()