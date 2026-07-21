"""SQLAlchemy 2.0 Async Engine, session factory, and DB health checking."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_async_engine() -> AsyncEngine:
    """Get or instantiate singleton AsyncEngine."""
    settings = get_settings()
    logger.info(
        "Initializing SQLAlchemy 2.0 AsyncEngine", db_url=settings.DATABASE_URL.split("@")[-1]
    )
    return create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or instantiate singleton async_sessionmaker."""
    engine = get_async_engine()
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    )


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an transactional async database session context."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_health() -> dict[str, Any]:
    """Verify PostgreSQL database connectivity and execute ping query."""
    engine = get_async_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            return {"status": "healthy", "ping": value == 1}
    except Exception as exc:
        logger.error("Database healthcheck failed", error=str(exc))
        return {"status": "unhealthy", "error": str(exc)}


async def close_db_engine() -> None:
    """Dispose AsyncEngine connections upon application shutdown."""
    if get_async_engine.cache_info().currsize > 0:
        logger.info("Disposing database AsyncEngine pool")
        engine = get_async_engine()
        await engine.dispose()
        get_async_engine.cache_clear()
        get_session_factory.cache_clear()
