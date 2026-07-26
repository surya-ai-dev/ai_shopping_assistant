"""SQLAlchemy Database Models Package.

This package exposes all Phase 6 database entities under a single import point.
It acts as the registry entry point, ensuring all mappings are registered on the
shared declarative base metadata.
"""

from src.models.base import BaseModel
from src.models.category import Category
from src.models.enums import (
    Currency,
    MerchantStatus,
    NotificationType,
    ProductStatus,
    ReviewSource,
    UserRole,
    WishlistVisibility,
)
from src.models.merchant import Merchant
from src.models.notification import Notification
from src.models.price_history import PriceHistory
from src.models.product import Product
from src.models.product_image import ProductImage
from src.models.product_price import ProductPrice
from src.models.product_review import ProductReview
from src.models.search_history import SearchHistory
from src.models.user import User
from src.models.wishlist import Wishlist
from src.models.wishlist_item import WishlistItem

__all__ = [
    "BaseModel",
    "User",
    "Merchant",
    "Category",
    "Product",
    "ProductImage",
    "ProductPrice",
    "PriceHistory",
    "ProductReview",
    "Wishlist",
    "WishlistItem",
    "SearchHistory",
    "Notification",
    "UserRole",
    "MerchantStatus",
    "ProductStatus",
    "Currency",
    "NotificationType",
    "ReviewSource",
    "WishlistVisibility",
]
