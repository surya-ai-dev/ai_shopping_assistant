"""Merchant Repository implementation for Phase 7.

This module houses the MerchantRepository class which handles custom data operations
for Merchant entities, including status changes and domain searches.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import interfaces

from src.models.enums import MerchantStatus
from src.models.merchant import Merchant
from src.repositories.base import BaseRepository


class MerchantRepository(BaseRepository[Merchant]):
    """Repository handling custom data operations for the Merchant entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize MerchantRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, Merchant)

    async def get_by_domain(
        self,
        domain: str,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
    ) -> Merchant | None:
        """Retrieve a merchant by its primary internet domain.

        Args:
            domain: Domain name (e.g., 'amazon.com').
            options: Loader options for eager relationship loading.

        Returns:
            The Merchant instance if found, otherwise None.
        """
        return await self.get_by_field("domain", domain, options=options)

    async def update_status(self, merchant_id: UUID, status: MerchantStatus) -> Merchant | None:
        """Update the operational status of a merchant.

        Args:
            merchant_id: Unique UUID of the merchant.
            status: Target MerchantStatus value.

        Returns:
            The updated Merchant instance, or None if merchant doesn't exist.
        """
        return await self.update(merchant_id, {"status": status})

    async def get_by_status(
        self,
        status: MerchantStatus,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Sequence[Merchant]:
        """Fetch all merchants matching a specific operational status.

        Args:
            status: Target MerchantStatus enum value.
            page: 1-based page index.
            page_size: limit per page.

        Returns:
            A sequence of matching Merchant instances.
        """
        return await self.get_all(filters={"status": status}, page=page, page_size=page_size)
