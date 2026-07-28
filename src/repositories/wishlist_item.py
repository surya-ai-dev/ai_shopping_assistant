"""WishlistItem Repository implementation for Phase 7.

This module houses the WishlistItemRepository class handling intersection queries,
alert threshold updates, and product loading within user wishlists.
"""

from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import interfaces

from src.core.exceptions import RepositoryError
from src.models.wishlist_item import WishlistItem
from src.repositories.base import BaseRepository


class WishlistItemRepository(BaseRepository[WishlistItem]):
    """Repository handling custom data operations for the WishlistItem entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize WishlistItemRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, WishlistItem)

    async def get_items_needing_alerts(
        self,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
    ) -> Sequence[WishlistItem]:
        """Fetch all wishlist items that have configured a desired_price threshold.

        Used by price monitoring cron workers.

        Args:
            options: Loader options for eager relationship loading.

        Returns:
            A sequence of WishlistItem instances.

        Raises:
            RepositoryError: If query fails.
        """
        try:
            stmt = select(WishlistItem).where(WishlistItem.desired_price.is_not(None))
            if options:
                stmt = stmt.options(*options)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as exc:
            raise RepositoryError(
                "Failed to fetch alert-triggered wishlist items",
                details={"error": str(exc)},
            ) from exc

    async def update_desired_price(
        self,
        wishlist_id: UUID,
        product_id: UUID,
        desired_price: Decimal | None,
    ) -> WishlistItem | None:
        """Update the target alert price of a saved item.

        Args:
            wishlist_id: Unique UUID of the wishlist.
            product_id: Unique UUID of the product.
            desired_price: New desired price alert threshold, or None to clear.

        Returns:
            The updated WishlistItem instance, or None if the item link doesn't exist.
        """
        item = await self.get_one_by({"wishlist_id": wishlist_id, "product_id": product_id})
        if not item:
            return None
        return await self.update(item.id, {"desired_price": desired_price})
