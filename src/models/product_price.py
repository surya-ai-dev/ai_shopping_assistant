"""SQLAlchemy ORM model for ProductPrice entity.

This module houses the ProductPrice table representing current merchant offers,
pricing, inventory state, and URLs.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.enums import Currency
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.merchant import Merchant
    from src.models.price_history import PriceHistory
    from src.models.product import Product


class ProductPrice(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """ProductPrice entity representing an active product listing at a specific merchant."""

    __tablename__ = "product_prices"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, native_enum=False),
        default=Currency.USD,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_in_stock: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    shipping_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="prices",
    )
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="prices",
    )
    price_histories: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory",
        back_populates="product_price",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint("product_id", "merchant_id", name="uq_product_merchant_price"),
        CheckConstraint("price >= 0", name="chk_product_price_non_negative"),
        CheckConstraint("shipping_cost >= 0", name="chk_product_shipping_cost_non_negative"),
    )
