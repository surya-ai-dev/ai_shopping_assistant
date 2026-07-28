"""Category Repository implementation for Phase 7.

This module houses the CategoryRepository class which handles hierarchical queries,
slug lookups, parent-child tree loading, and category list operations.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import interfaces, selectinload

from src.core.exceptions import RepositoryError
from src.models.category import Category
from src.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository handling custom data operations for the Category entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize CategoryRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, Category)

    async def get_by_slug(
        self,
        slug: str,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
    ) -> Category | None:
        """Retrieve a category by its URL-friendly slug.

        Args:
            slug: Category slug text (e.g. 'smart-phones').
            options: Loader options for eager relationship loading.

        Returns:
            The Category instance if found, otherwise None.
        """
        return await self.get_by_field("slug", slug, options=options)

    async def get_root_categories(
        self,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
    ) -> Sequence[Category]:
        """Fetch all root categories (categories with no parent).

        Args:
            options: Loader options for eager relationship loading.

        Returns:
            A sequence of root Category instances.
        """
        return await self.get_all(filters={"parent_id": None}, options=options)

    async def get_subcategories(
        self,
        parent_id: UUID,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
    ) -> Sequence[Category]:
        """Fetch immediate subcategories of a parent category.

        Args:
            parent_id: Unique UUID of the parent category.
            options: Loader options for eager relationship loading.

        Returns:
            A sequence of child Category instances.
        """
        return await self.get_all(filters={"parent_id": parent_id}, options=options)

    async def get_subcategory_tree(self, parent_id: UUID) -> Category | None:
        """Fetch a category and eagerly load its recursive children tree.

        To prevent recursive database calls, we use selectinload on children relationships,
        enabling SQLAlchemy to resolve nested subtrees efficiently in a single step.

        Args:
            parent_id: Unique UUID of the root node category.

        Returns:
            The Category instance with fully populated children collections, or None.

        Raises:
            RepositoryError: If a database query fails.
        """
        try:
            # We eager load children, and children's children to support a 3-level deep tree
            stmt = (
                select(Category)
                .options(selectinload(Category.children).selectinload(Category.children))
                .where(Category.id == parent_id)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            raise RepositoryError(
                f"Failed to load subcategory tree for {parent_id}",
                details={"error": str(exc)},
            ) from exc
