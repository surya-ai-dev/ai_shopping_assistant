"""SearchHistory Repository implementation for Phase 7.

This module houses the SearchHistoryRepository class providing queries for user search history
tracking, recent search retrievals, and trending keyword aggregation.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import RepositoryError
from src.models.search_history import SearchHistory
from src.repositories.base import BaseRepository


class SearchHistoryRepository(BaseRepository[SearchHistory]):
    """Repository handling custom data operations for the SearchHistory entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize SearchHistoryRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, SearchHistory)

    async def get_recent_searches(
        self,
        user_id: UUID,
        *,
        limit: int = 5,
    ) -> Sequence[SearchHistory]:
        """Fetch the most recent search queries executed by a user.

        Args:
            user_id: Unique UUID of the user.
            limit: Maximum count to return (default 5).

        Returns:
            A sequence of SearchHistory instances sorted by date descending.
        """
        return await self.get_all(
            filters={"user_id": user_id},
            sort_by=["-searched_at"],
            limit=limit,
        )

    async def get_popular_queries(
        self,
        *,
        limit: int = 10,
    ) -> Sequence[tuple[str, int]]:
        """Retrieve the most popular search query strings across all users.

        This uses SQL aggregation to count occurances of query terms.

        Args:
            limit: Maximum count of trending keywords to return.

        Returns:
            A sequence of tuples containing (query_text, count).

        Raises:
            RepositoryError: If the aggregation query fails.
        """
        try:
            stmt = (
                select(SearchHistory.query, func.count(SearchHistory.id).label("query_count"))
                .group_by(SearchHistory.query)
                .order_by(func.count(SearchHistory.id).desc())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return [(row[0], row[1]) for row in result.all()]
        except Exception as exc:
            raise RepositoryError(
                "Failed to retrieve popular search queries",
                details={"error": str(exc)},
            ) from exc
