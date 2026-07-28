"""ProductPrice Repository implementation for Phase 7.

This module houses the ProductPriceRepository class providing custom queries for active merchant
price offers, stock validation, and best-deal aggregations.
"""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import interfaces, joinedload
from sqlalchemy.orm.interfaces import ORMOption

from src.models.product_price import ProductPrice
from src.repositories.base import BaseRepository


class ProductPriceRepository(BaseRepository[ProductPrice]):
    """Repository handling custom data operations for the ProductPrice entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize ProductPriceRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, ProductPrice)

    async def get_active_offers(
        self,
        product_id: UUID,
        *,
        only_in_stock: bool = False,
        options: Sequence[ORMOption] | None = None,
    ) -> Sequence[ProductPrice]:
        """Retrieve all active pricing offers for a product, sorted by cheapest price first.

        Loads merchant details by default using joinedload to prevent N+1 queries.

        Args:
            product_id: Unique UUID of the product.
            only_in_stock: If True, filters out out-of-stock listings.
            options: Loader options for relationship loading.

        Returns:
            A sequence of ProductPrice instances sorted by price ascending.
        """
        filters: dict[str, Any] = {"product_id": product_id}
        if only_in_stock:
            filters["is_in_stock"] = True

        # Default to loading merchant details to render store names/domains on pages
        loader_options: list[ORMOption] = list(options) if options else []
        if not any(
            isinstance(opt, interfaces.LoaderOption) and "merchant" in str(opt)
            for opt in loader_options
        ):
            loader_options.append(joinedload(ProductPrice.merchant))

        return await self.get_all(
            filters=filters,
            sort_by=["price", "-last_updated"],
            options=loader_options,
        )

    async def get_by_merchant(self, merchant_id: UUID) -> Sequence[ProductPrice]:
        """Fetch all pricing listings offered by a specific merchant.

        Args:
            merchant_id: Unique UUID of the merchant.

        Returns:
            A sequence of ProductPrice instances.
        """
        return await self.get_all(filters={"merchant_id": merchant_id})
