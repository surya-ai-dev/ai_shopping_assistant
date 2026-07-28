"""SQLAlchemy Async Engine connection management."""

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from src.core.logging import get_logger
from src.database.config import get_db_config

logger = get_logger(__name__)


@lru_cache
def get_async_engine() -> AsyncEngine:
    """Get or instantiate singleton AsyncEngine."""
    config = get_db_config()
    logger.info("Initializing SQLAlchemy AsyncEngine for PostgreSQL")
    return create_async_engine(
        config.url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


async def close_db_engine() -> None:
    """Dispose AsyncEngine connections upon application shutdown."""
    if get_async_engine.cache_info().currsize > 0:
        logger.info("Disposing database AsyncEngine pool")
        engine = get_async_engine()
        await engine.dispose()
        get_async_engine.cache_clear()
