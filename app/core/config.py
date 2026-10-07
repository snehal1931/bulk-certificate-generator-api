"""Core configuration module using pydantic-settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    APP_NAME: str = "Bulk Certificate Generator API"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./certificate_generator.db"

    # Storage
    STORAGE_DIR: Path = Path("storage/certificates")

    # Processing Limits
    MAX_RECIPIENTS_PER_JOB: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_absolute_storage_dir(self) -> Path:
        """Ensure storage directory exists and return absolute Path."""
        path = self.STORAGE_DIR.resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
