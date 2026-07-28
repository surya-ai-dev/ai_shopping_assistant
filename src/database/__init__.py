"""Database management package initialization."""

from src.database.base import Base
from src.database.connection import close_db_engine, get_async_engine
from src.database.session import get_async_session, get_session_factory

__all__ = [
    "Base",
    "close_db_engine",
    "get_async_engine",
    "get_async_session",
    "get_session_factory",
]


async def init_db() -> None:
    """Initialize database tables."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
