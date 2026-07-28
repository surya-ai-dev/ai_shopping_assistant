"""Wishlist Repository implementation for Phase 7.

This module houses the WishlistRepository class providing custom queries for user wishlists,
adding/removing products, and wishlist visibility controls.
"""

from collections.abc import Sequence
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import interfaces

from src.core.exceptions import RepositoryError
from src.models.wishlist import Wishlist
from src.models.wishlist_item import WishlistItem
from src.repositories.base import BaseRepository


class WishlistRepository(BaseRepository[Wishlist]):
    """Repository handling custom data operations for the Wishlist entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize WishlistRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, Wishlist)

    async def get_user_wishlists(
        self,
        user_id: UUID,
        *,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
    ) -> Sequence[Wishlist]:
        """Fetch all wishlists created by a specific user.

        Args:
            user_id: Unique UUID of the user.
            options: Loader options for relationship loading.

        Returns:
            A sequence of Wishlist instances.
        """
        return await self.get_all(filters={"user_id": user_id}, options=options)

    async def add_product(
        self,
        wishlist_id: UUID,
        product_id: UUID,
        *,
        desired_price: Decimal | None = None,
    ) -> WishlistItem:
        """Add a product link to a wishlist.

        This creates a WishlistItem intersection link. If a duplicate exists,
        it raises a RepositoryError.

        Args:
            wishlist_id: Unique UUID of the wishlist.
            product_id: Unique UUID of the product to link.
            desired_price: Optional target price trigger for price drop alerts.

        Returns:
            The created WishlistItem record.

        Raises:
            RepositoryError: If adding the item violates constraints.
        """
        try:
            # We check if it is already added to prevent duplicate keys
            stmt = select(WishlistItem).where(
                WishlistItem.wishlist_id == wishlist_id,
                WishlistItem.product_id == product_id,
            )
            res = await self.session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                raise RepositoryError("Product is already present in this wishlist.")

            # Create intersection record
            item = WishlistItem(
                wishlist_id=wishlist_id,
                product_id=product_id,
                desired_price=desired_price,
            )
            self.session.add(item)
            await self.session.flush()
            return item
        except Exception as exc:
            await self.session.rollback()
            raise RepositoryError(
                f"Failed to add product {product_id} to wishlist {wishlist_id}",
                details={"error": str(exc)},
            ) from exc

    async def remove_product(self, wishlist_id: UUID, product_id: UUID) -> bool:
        """Remove a product link from a wishlist.

        Args:
            wishlist_id: Unique UUID of the wishlist.
            product_id: Unique UUID of the product.

        Returns:
            True if the link existed and was removed, otherwise False.

        Raises:
            RepositoryError: If database delete fails.
        """
        try:
            stmt = delete(WishlistItem).where(
                WishlistItem.wishlist_id == wishlist_id,
                WishlistItem.product_id == product_id,
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
            rowcount = getattr(result, "rowcount", 0)
            return (rowcount if rowcount is not None else 0) > 0
        except Exception as exc:
            await self.session.rollback()
            raise RepositoryError(
                f"Failed to remove product {product_id} from wishlist {wishlist_id}",
                details={"error": str(exc)},
            ) from exc
