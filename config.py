# config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings."""

    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/pulse"
    WEBHOOK_URL: str | None = None
    USER_AGENT: str = "PulsePipeline/1.0 (+https://github.com/yourorg/pulse-pipeline)"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

