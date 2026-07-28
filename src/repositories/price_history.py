"""PriceHistory Repository implementation for Phase 7.

This module houses the PriceHistoryRepository class providing queries for time-series price
trends, charting historical points, and finding minimum/maximum price points.
"""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import RepositoryError
from src.models.price_history import PriceHistory
from src.repositories.base import BaseRepository


class PriceHistoryRepository(BaseRepository[PriceHistory]):
    """Repository handling custom data operations for the PriceHistory entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize PriceHistoryRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, PriceHistory)

    async def get_price_trends(
        self,
        product_price_id: UUID,
        *,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Sequence[PriceHistory]:
        """Retrieve price history data points for charting, sorted chronologically.

        Args:
            product_price_id: Unique UUID of the merchant listing offer.
            start_date: Optional filter to pull points starting from this timestamp.
            end_date: Optional filter to limit points up to this timestamp.

        Returns:
            A sequence of PriceHistory instances sorted by recorded_at ascending.

        Raises:
            RepositoryError: If a database query fails.
        """
        try:
            stmt = select(PriceHistory).where(PriceHistory.product_price_id == product_price_id)

            if start_date:
                stmt = stmt.where(PriceHistory.recorded_at >= start_date)
            if end_date:
                stmt = stmt.where(PriceHistory.recorded_at <= end_date)

            # Sort chronologically for charting engines
            stmt = stmt.order_by(PriceHistory.recorded_at.asc())

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch price trends for listing {product_price_id}",
                details={"error": str(exc)},
            ) from exc

    async def get_min_max_prices(
        self,
        product_price_id: UUID,
    ) -> tuple[Decimal, Decimal] | None:
        """Fetch the minimum (cheapest) and maximum (most expensive) recorded prices.

        Args:
            product_price_id: Unique UUID of the merchant listing offer.

        Returns:
            A tuple of (min_price, max_price), or None if no history exists.

        Raises:
            RepositoryError: If a query fails.
        """
        try:
            stmt = select(
                func.min(PriceHistory.price),
                func.max(PriceHistory.price),
            ).where(PriceHistory.product_price_id == product_price_id)

            result = await self.session.execute(stmt)
            row = result.fetchone()
            if row and row[0] is not None and row[1] is not None:
                return Decimal(str(row[0])), Decimal(str(row[1]))
            return None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to retrieve min/max bounds for listing {product_price_id}",
                details={"error": str(exc)},
            ) from exc
