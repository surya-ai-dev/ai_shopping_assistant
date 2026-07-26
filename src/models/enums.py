"""Strongly typed enums for Phase 6 Database Models.

This module houses all enumerations used to enforce database integrity and state bounds.
We implement them as StrEnum for clean string comparison and JSON serialization.
"""

from enum import StrEnum


class UserRole(StrEnum):
    """Access control roles for application users."""

    ADMIN = "admin"
    STAFF = "staff"
    USER = "user"


class MerchantStatus(StrEnum):
    """Operational status of a merchant platform."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class ProductStatus(StrEnum):
    """Lifecycle status of a product within the catalog."""

    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class Currency(StrEnum):
    """Supported transaction and tracking currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    CAD = "CAD"
    AUD = "AUD"


class NotificationType(StrEnum):
    """Classification of sent notifications."""

    PRICE_DROP = "price_drop"
    BACK_IN_STOCK = "back_in_stock"
    SYSTEM = "system"
    PROMO = "promo"


class ReviewSource(StrEnum):
    """Origin source of a product review."""

    INTERNAL = "internal"
    EXTERNAL = "external"


class WishlistVisibility(StrEnum):
    """Privacy status of a user's wishlist."""

    PRIVATE = "private"
    PUBLIC = "public"
    SHARED = "shared"
