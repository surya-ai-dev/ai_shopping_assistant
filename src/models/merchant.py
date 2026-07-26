"""SQLAlchemy ORM model for Merchant entity.

This module houses the Merchant table, representing e-commerce retailers,
their operational state, and scraper/API configurations.
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.enums import MerchantStatus
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.product_price import ProductPrice


class Merchant(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Merchant entity representing retail platforms like Amazon or Best Buy."""

    __tablename__ = "merchants"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    status: Mapped[MerchantStatus] = mapped_column(
        Enum(MerchantStatus, native_enum=False),
        default=MerchantStatus.ACTIVE,
        nullable=False,
    )
    logo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    api_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Relationships
    prices: Mapped[list["ProductPrice"]] = relationship(
        "ProductPrice",
        back_populates="merchant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
