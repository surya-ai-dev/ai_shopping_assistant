"""SQLAlchemy Repositories package.

This package exposes all Phase 7 database repositories under a single import point.
It implements the Repository Pattern to decouple database-specific logic from the
upcoming Service Layer.
"""

from src.repositories.base import BaseRepository
from src.repositories.category import CategoryRepository
from src.repositories.merchant import MerchantRepository
from src.repositories.notification import NotificationRepository
from src.repositories.price_history import PriceHistoryRepository
from src.repositories.product import ProductRepository
from src.repositories.product_image import ProductImageRepository
from src.repositories.product_price import ProductPriceRepository
from src.repositories.product_review import ProductReviewRepository
from src.repositories.search_history import SearchHistoryRepository
from src.repositories.user import UserRepository
from src.repositories.wishlist import WishlistRepository
from src.repositories.wishlist_item import WishlistItemRepository

__all__ = [
    "BaseRepository",
    "CategoryRepository",
    "MerchantRepository",
    "NotificationRepository",
    "PriceHistoryRepository",
    "ProductImageRepository",
    "ProductPriceRepository",
    "ProductRepository",
    "ProductReviewRepository",
    "SearchHistoryRepository",
    "UserRepository",
    "WishlistItemRepository",
    "WishlistRepository",
]
