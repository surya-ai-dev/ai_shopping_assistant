"""Environment configuration management powered by Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application global environment settings schema."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General System
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    APP_NAME: str = Field(default="ai_shopping_copilot_scraper")

    # Database Settings
    POSTGRES_USER: str = Field(default="scraper_user")
    POSTGRES_PASSWORD: str = Field(default="scraper_password")
    POSTGRES_DB: str = Field(default="scraper_db")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://scraper_user:scraper_password@localhost:5432/scraper_db"
    )

    # Playwright Browser Pool Settings
    BROWSER_HEADLESS: bool = Field(default=True)
    BROWSER_MAX_INSTANCES: int = Field(default=3)
    BROWSER_MAX_CONTEXTS_PER_BROWSER: int = Field(default=5)
    BROWSER_MAX_PAGES_PER_CONTEXT: int = Field(default=10)
    BROWSER_NAVIGATION_TIMEOUT_MS: int = Field(default=30000)

    # Request Manager & Throttling
    RATE_LIMIT_PER_MINUTE: int = Field(default=30)
    MAX_RETRIES: int = Field(default=3)
    RETRY_BACKOFF_FACTOR: float = Field(default=2.0)
    JITTER_RANGE_MS: int = Field(default=500)
    RANDOM_DELAY_MIN_MS: int = Field(default=1000)
    RANDOM_DELAY_MAX_MS: int = Field(default=3000)

    # Raw Payload Storage
    RAW_STORAGE_DIR: Path = Field(default=Path("data/raw_payloads"))
    RAW_STORAGE_MODE: str = Field(default="filesystem")  # filesystem | database | both

    # Queue & Worker Settings
    WORKER_CONCURRENCY: int = Field(default=5)
    QUEUE_MAX_SIZE: int = Field(default=10000)

    # Observability
    OTEL_SERVICE_NAME: str = Field(default="ai-shopping-scraper")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(default="http://localhost:4318")
    PROMETHEUS_METRICS_ENABLED: bool = Field(default=True)
    PROMETHEUS_METRICS_PORT: int = Field(default=8000)


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton instance of Settings."""
    return Settings()
