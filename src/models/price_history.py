"""SQLAlchemy ORM model for PriceHistory entity.

This module houses the PriceHistory table representing a time-series log of
price and stock changes for merchant offers.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.enums import Currency
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.product_price import ProductPrice


class PriceHistory(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """PriceHistory entity representing a price audit point in time."""

    __tablename__ = "price_history"

    product_price_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product_prices.id", ondelete="CASCADE"),
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
    is_in_stock: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    product_price: Mapped["ProductPrice"] = relationship(
        "ProductPrice",
        back_populates="price_histories",
    )

    __table_args__ = (
        Index("idx_price_history_price_recorded", "product_price_id", "recorded_at"),
        CheckConstraint("price >= 0", name="chk_price_history_non_negative"),
    )
