"""SQLAlchemy ORM model for Product entity.

This module houses the canonical Product table representing items in the catalog,
their specifications (via JSONB attributes), and relationships.
"""

import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.enums import ProductStatus
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.category import Category
    from src.models.product_image import ProductImage
    from src.models.product_price import ProductPrice
    from src.models.product_review import ProductReview
    from src.models.wishlist_item import WishlistItem


class Product(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Product entity representing a canonical product in the system."""

    __tablename__ = "products"

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    brand: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(
        String(100),
        index=True,
        nullable=True,
    )
    sku: Mapped[str | None] = mapped_column(
        String(128),
        index=True,
        nullable=True,
    )
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, native_enum=False),
        default=ProductStatus.ACTIVE,
        nullable=False,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    attributes: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Relationships
    category: Mapped[Optional["Category"]] = relationship(
        "Category",
        back_populates="products",
    )
    images: Mapped[list["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ProductImage.position.asc()",
    )
    prices: Mapped[list["ProductPrice"]] = relationship(
        "ProductPrice",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    reviews: Mapped[list["ProductReview"]] = relationship(
        "ProductReview",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    wishlist_items: Mapped[list["WishlistItem"]] = relationship(
        "WishlistItem",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_products_title_trgm", "title", postgresql_ops={"title": "gin_trgm_ops"}, postgresql_using="gin"),
        Index("idx_products_attributes_gin", "attributes", postgresql_using="gin"),
    )
