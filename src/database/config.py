"""Database configuration module for PostgreSQL connection."""

import os
from src.config.settings import get_settings


class DatabaseConfig:
    """Database configuration options."""

    def __init__(self) -> None:
        settings = get_settings()
        self.url: str = os.getenv("DATABASE_URL", settings.DATABASE_URL)
        # Ensure database URL is compatible with asyncpg
        if self.url.startswith("postgresql://"):
            self.url = self.url.replace("postgresql://", "postgresql+asyncpg://", 1)


def get_db_config() -> DatabaseConfig:
    """Get database configuration instance."""
    return DatabaseConfig()
