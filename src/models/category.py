"""SQLAlchemy ORM model for Category entity.

This module houses the self-referential Category table, representing a
hierarchical category taxonomy tree for product organization.
"""

from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.product import Product


class Category(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Category entity representing a hierarchical node in the product taxonomy."""

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        index=True,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )

    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="category",
        cascade="save-update, merge",
    )

    __table_args__ = (
        UniqueConstraint("name", "parent_id", name="uq_categories_name_parent"),
    )
