"""ProductImage Repository implementation for Phase 7.

This module houses the ProductImageRepository class handling image retrieval
by position ordering and bulk position updating.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.product_image import ProductImage
from src.repositories.base import BaseRepository


class ProductImageRepository(BaseRepository[ProductImage]):
    """Repository handling custom data operations for the ProductImage entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize ProductImageRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, ProductImage)

    async def get_sorted_images(self, product_id: UUID) -> Sequence[ProductImage]:
        """Fetch all images for a product sorted by their display position.

        Args:
            product_id: Unique UUID of the product.

        Returns:
            A sequence of ProductImage instances sorted by position.
        """
        return await self.get_all(
            filters={"product_id": product_id},
            sort_by=["position", "created_at"],
        )

    async def update_positions(self, image_position_map: dict[UUID, int]) -> None:
        """Bulk update display positions for a set of images in a single transaction.

        Args:
            image_position_map: A dictionary mapping image UUIDs to their target position index.
        """
        for img_id, pos in image_position_map.items():
            await self.update(img_id, {"position": pos})
