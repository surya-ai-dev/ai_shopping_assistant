"""SQLAlchemy ORM model for ProductReview entity.

This module houses the ProductReview table representing user-written or
scraped merchant reviews for sentiment parsing and catalog ratings.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.enums import ReviewSource
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.product import Product
    from src.models.user import User


class ProductReview(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """ProductReview entity representing a customer or external site review."""

    __tablename__ = "product_reviews"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    rating: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    author_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    source: Mapped[ReviewSource] = mapped_column(
        Enum(ReviewSource, native_enum=False),
        default=ReviewSource.INTERNAL,
        nullable=False,
    )
    review_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="reviews",
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="reviews",
    )

    __table_args__ = (
        CheckConstraint("rating >= 0.0 AND rating <= 5.0", name="chk_product_review_rating_range"),
        Index("idx_product_reviews_rating", "product_id", "rating"),
    )
