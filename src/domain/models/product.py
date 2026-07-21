"""Pydantic v2 domain models for Product entities, Price History, and Fingerprints."""

import hashlib
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.domain.enums import CategoryEnum, CurrencyEnum
from src.domain.models.specs import GenericProductSpecs, LaptopSpecs, MobileSpecs


class PriceHistory(BaseModel):
    """Historical price entry model."""

    id: str | None = None
    product_id: str | None = None
    price: float = Field(..., ge=0.0, description="Product price value")
    original_price: float | None = Field(default=None, ge=0.0, description="List/MSRP price")
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD, description="Currency code")
    is_in_stock: bool = Field(default=True, description="Availability status")
    discount_percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    seller_name: str | None = Field(default=None, description="Merchant seller name")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProductFingerprint(BaseModel):
    """Fingerprint used for cross-site product duplicate detection."""

    hash_key: str = Field(..., description="Deterministic SHA256 hex string")
    brand: str
    normalized_model: str
    category: CategoryEnum

    @classmethod
    def generate(
        cls, brand: str, model: str, category: CategoryEnum, key_spec: str = ""
    ) -> "ProductFingerprint":
        """Generate a deterministic fingerprint hash key."""
        clean_brand = brand.strip().lower()
        clean_model = model.strip().lower()
        raw_key = f"{clean_brand}:{clean_model}:{category.value}:{key_spec.strip().lower()}"
        hash_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return cls(
            hash_key=hash_key,
            brand=clean_brand,
            normalized_model=clean_model,
            category=category,
        )


class Product(BaseModel):
    """Core domain model representing a normalized product listing."""

    id: str | None = Field(default=None, description="Database unique UUID identifier")
    site_id: str = Field(..., description="Target site identifier e.g. amazon_us, bestbuy")
    url: str = Field(..., description="Product canonical URL")
    sku: str | None = Field(default=None, description="Store SKU or ASIN")
    title: str = Field(..., min_length=2, description="Product listing title")
    brand: str = Field(..., min_length=1, description="Brand manufacturer name")
    model_name: str = Field(..., min_length=1, description="Model designation")
    category: CategoryEnum = Field(..., description="Domain category e.g. laptop or mobile")

    current_price: float = Field(..., ge=0.0, description="Latest price value")
    original_price: float | None = Field(default=None, ge=0.0)
    currency: CurrencyEnum = Field(default=CurrencyEnum.USD)
    is_in_stock: bool = Field(default=True)

    rating: float | None = Field(default=None, ge=0.0, le=5.0, description="Product user rating")
    review_count: int | None = Field(default=None, ge=0, description="Total review count")

    image_urls: list[str] = Field(default_factory=list, description="Product image URLs")
    raw_payload_id: str | None = Field(
        default=None, description="Reference ID to saved raw HTML/JSON"
    )

    specs: LaptopSpecs | MobileSpecs | GenericProductSpecs = Field(
        default_factory=GenericProductSpecs, description="Structured technical specifications"
    )
    price_history: list[PriceHistory] = Field(default_factory=list)
    fingerprint: ProductFingerprint | None = Field(default=None)

    metadata: dict[str, Any] = Field(default_factory=dict, description="Scraper metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("title", "brand", "model_name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Sanitize text fields by stripping leading/trailing whitespace."""
        return v.strip()
