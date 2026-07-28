"""SQLAlchemy ORM model for ProductImage entity.

This module houses the ProductImage table, representing product-associated
images, alt-text descriptions, and ordering sequences.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.product import Product


class ProductImage(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """ProductImage entity representing an image URL associated with a product."""

    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    alt_text: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="images",
    )
