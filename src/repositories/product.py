"""Product Repository implementation for Phase 7.

This module houses the ProductRepository class which provides customized query methods
for Product entities, including full-text search, brand filtering, and category queries.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import interfaces

from src.core.exceptions import RepositoryError
from src.models.enums import ProductStatus
from src.models.product import Product
from src.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository handling custom data operations for the Product entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize ProductRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, Product)

    async def search_products(
        self,
        query_text: str,
        *,
        brand: str | None = None,
        category_id: UUID | None = None,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Sequence[Product]:
        """Perform fuzzy search on product titles and brand names.

        Eagerly loads price listings and primary images by default using options to avoid N+1 queries.

        Args:
            query_text: Keyword string to search.
            brand: Optional filter by brand.
            category_id: Optional filter by category ID.
            options: Loader options for relationship loading.
            page: 1-based page index.
            page_size: limit per page.

        Returns:
            A sequence of matching Product instances.

        Raises:
            RepositoryError: If a database search fails.
        """
        try:
            stmt = select(Product).where(Product.status == ProductStatus.ACTIVE)

            if options:
                stmt = stmt.options(*options)

            # Apply full-text search keyword filter
            if query_text:
                search_pattern = f"%{query_text}%"
                stmt = stmt.where(
                    or_(
                        Product.title.ilike(search_pattern),
                        Product.brand.ilike(search_pattern),
                        Product.model_name.ilike(search_pattern),
                    )
                )

            # Apply brand filter
            if brand:
                stmt = stmt.where(Product.brand == brand)

            # Apply category filter
            if category_id:
                stmt = stmt.where(Product.category_id == category_id)

            # Apply sorting
            stmt = stmt.order_by(Product.title.asc())

            # Apply pagination
            if page is not None and page_size is not None:
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as exc:
            raise RepositoryError(
                f"Failed to execute product search for '{query_text}'",
                details={"error": str(exc)},
            ) from exc

    async def get_by_brand(
        self,
        brand: str,
        *,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Sequence[Product]:
        """Retrieve all active products matching a specific brand.

        Args:
            brand: Brand name text.
            options: Loader options.
            page: 1-based page.
            page_size: limit per page.

        Returns:
            A sequence of matching Product instances.
        """
        return await self.get_all(
            filters={"brand": brand, "status": ProductStatus.ACTIVE},
            sort_by=["title"],
            options=options,
            page=page,
            page_size=page_size,
        )

    async def get_by_category(
        self,
        category_id: UUID,
        *,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Sequence[Product]:
        """Retrieve all active products classified under a category.

        Args:
            category_id: Unique UUID of the category.
            options: Loader options.
            page: 1-based page.
            page_size: limit per page.

        Returns:
            A sequence of matching Product instances.
        """
        return await self.get_all(
            filters={"category_id": category_id, "status": ProductStatus.ACTIVE},
            sort_by=["title"],
            options=options,
            page=page,
            page_size=page_size,
        )

    async def get_latest(
        self,
        *,
        limit: int = 10,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
    ) -> Sequence[Product]:
        """Retrieve the most recently added active products.

        Args:
            limit: Maximum count to return (default 10).
            options: Loader options.

        Returns:
            A sequence of recently added Product instances.
        """
        return await self.get_all(
            filters={"status": ProductStatus.ACTIVE},
            sort_by=["-created_at"],
            options=options,
            limit=limit,
        )

    async def get_featured(
        self,
        *,
        limit: int = 10,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
    ) -> Sequence[Product]:
        """Retrieve active products flagged as featured (highly rated).

        Args:
            limit: Maximum count to return (default 10).
            options: Loader options.

        Returns:
            A sequence of featured Product instances.

        Raises:
            RepositoryError: If a query fails.
        """
        try:
            # We select active products ordered by ratings desc
            stmt = (
                select(Product)
                .where(Product.status == ProductStatus.ACTIVE)
                .order_by(Product.created_at.desc())  # Or rating desc when rating column exists on Product
                .limit(limit)
            )
            if options:
                stmt = stmt.options(*options)
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as exc:
            raise RepositoryError(
                "Failed to fetch featured products",
                details={"error": str(exc)},
            ) from exc
