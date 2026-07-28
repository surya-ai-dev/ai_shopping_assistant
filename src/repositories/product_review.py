"""ProductReview Repository implementation for Phase 7.

This module houses the ProductReviewRepository class providing custom queries for reviews,
rating filters, and aggregate rating averages.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import RepositoryError
from src.models.enums import ReviewSource
from src.models.product_review import ProductReview
from src.repositories.base import BaseRepository


class ProductReviewRepository(BaseRepository[ProductReview]):
    """Repository handling custom data operations for the ProductReview entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize ProductReviewRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, ProductReview)

    async def get_reviews_by_rating(
        self,
        product_id: UUID,
        rating: float,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Sequence[ProductReview]:
        """Fetch all reviews for a product matching a specific rating tier.

        Args:
            product_id: Unique UUID of the product.
            rating: Rating tier (e.g. 5.0).
            page: 1-based page.
            page_size: limit per page.

        Returns:
            A sequence of matching ProductReview instances.
        """
        return await self.get_all(
            filters={"product_id": product_id, "rating": rating},
            sort_by=["-review_date"],
            page=page,
            page_size=page_size,
        )

    async def get_reviews_by_source(
        self,
        product_id: UUID,
        source: ReviewSource,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Sequence[ProductReview]:
        """Fetch reviews originating from a specific source (e.g., scraped vs internal).

        Args:
            product_id: Unique UUID of the product.
            source: ReviewSource enum value.
            page: 1-based page.
            page_size: limit per page.

        Returns:
            A sequence of matching ProductReview instances.
        """
        return await self.get_all(
            filters={"product_id": product_id, "source": source},
            sort_by=["-review_date"],
            page=page,
            page_size=page_size,
        )

    async def get_average_rating(self, product_id: UUID) -> float:
        """Calculate the average rating and review count of a product in SQL.

        This avoids loading large lists of reviews into Python application memory,
        shifting aggregate calculations to the database engine.

        Args:
            product_id: Unique UUID of the product.

        Returns:
            A float representing the average rating. Defaults to 0.0 if no reviews exist.

        Raises:
            RepositoryError: If the SQL calculation fails.
        """
        try:
            stmt = select(func.avg(ProductReview.rating)).where(
                ProductReview.product_id == product_id
            )
            result = await self.session.execute(stmt)
            val = result.scalar()
            return float(val) if val is not None else 0.0
        except Exception as exc:
            raise RepositoryError(
                f"Failed to calculate rating average for product {product_id}",
                details={"error": str(exc)},
            ) from exc
