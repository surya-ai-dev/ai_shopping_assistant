"""SQLAlchemy 2.0 ORM Mapped Models for Products, Specs, Price History, and Fingerprints."""

import uuid
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.base import Base, TimestampMixin


class ProductORM(Base, TimestampMixin):
    """Product master table mapped ORM entity."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    url: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    sku: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    original_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    is_in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    image_urls: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    raw_payload_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    specs: Mapped["ProductSpecORM"] = relationship(
        "ProductSpecORM", back_populates="product", uselist=False, cascade="all, delete-orphan"
    )
    price_history: Mapped[list["PriceHistoryORM"]] = relationship(
        "PriceHistoryORM",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="PriceHistoryORM.created_at.desc()",
    )
    fingerprint: Mapped["ProductFingerprintORM"] = relationship(
        "ProductFingerprintORM",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_product_site_brand", "site_id", "brand"),
        Index("idx_product_category", "category"),
    )


class ProductSpecORM(Base, TimestampMixin):
    """Product technical specification details mapped table."""

    __tablename__ = "product_specs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    product: Mapped["ProductORM"] = relationship("ProductORM", back_populates="specs")


class PriceHistoryORM(Base, TimestampMixin):
    """Price audit log and trend history mapped table."""

    __tablename__ = "price_history"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    original_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    is_in_stock: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    seller_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    product: Mapped["ProductORM"] = relationship("ProductORM", back_populates="price_history")


class ProductFingerprintORM(Base, TimestampMixin):
    """Cross-site product duplicate detection hash table."""

    __tablename__ = "product_fingerprints"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    hash_key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(128), nullable=False)
    normalized_model: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)

    product: Mapped["ProductORM"] = relationship("ProductORM", back_populates="fingerprint")


class RawPayloadORM(Base, TimestampMixin):
    """Database fallback store for raw web HTML/JSON payloads."""

    __tablename__ = "raw_payloads"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    site_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    html_content: Mapped[str] = mapped_column(Text, nullable=False)
