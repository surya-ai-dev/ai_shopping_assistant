"""Base async SQLAlchemy repository implementation."""

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from src.interfaces.repository import BaseRepository

T = TypeVar("T")


class BaseSQLAlchemyRepository(BaseRepository[T], Generic[T]):
    """Base Async SQLAlchemy Repository implementation providing session context."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
