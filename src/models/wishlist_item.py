"""SQLAlchemy ORM model for WishlistItem entity.

This module houses the WishlistItem intersection table linking wishlists to products,
with support for target alerts (desired_price).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.product import Product
    from src.models.wishlist import Wishlist


class WishlistItem(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """WishlistItem entity representing a product saved in a user's wishlist."""

    __tablename__ = "wishlist_items"

    wishlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("wishlists.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    desired_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    wishlist: Mapped["Wishlist"] = relationship(
        "Wishlist",
        back_populates="items",
    )
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="wishlist_items",
    )

    __table_args__ = (
        UniqueConstraint("wishlist_id", "product_id", name="uq_wishlist_product_item"),
        CheckConstraint("desired_price >= 0", name="chk_wishlist_item_desired_price_non_negative"),
    )
