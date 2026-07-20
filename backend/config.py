"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings.

    Values are read from environment variables (and an optional ``.env`` file).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AI News Aggregator"
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+psycopg2://news:news@localhost:5432/news_aggregator"

    # Auth
    jwt_secret_key: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Ingestion / scheduler
    ingest_interval_minutes: int = 60
    enable_scheduler: bool = True
    max_articles_per_feed: int = 20

    # Digest email
    digest_hour: int = 7
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "AI News Aggregator <noreply@example.com>"

    # Frontend
    api_base_url: str = "http://localhost:8000"

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_username and self.smtp_password)


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()


settings = get_settings()
