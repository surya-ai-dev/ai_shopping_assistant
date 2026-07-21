"""Async Repository Interfaces adhering to Clean Architecture and Repository Pattern."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

from src.domain.enums import URLStatusEnum
from src.domain.models.crawl import CrawlJob, CrawlSchedule
from src.domain.models.product import Product
from src.domain.models.url import DiscoveredURL

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Generic async repository interface for CRUD operations."""

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> T | None:
        """Fetch an entity by its unique ID."""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Create or update an entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        pass


class ProductRepositoryInterface(BaseRepository[Product]):
    """Domain repository interface for Product persistence operations."""

    @abstractmethod
    async def get_by_url(self, url: str) -> Product | None:
        """Retrieve product by canonical URL."""
        pass

    @abstractmethod
    async def get_by_fingerprint(self, hash_key: str) -> Product | None:
        """Retrieve product by fingerprint hash key."""
        pass

    @abstractmethod
    async def upsert_product(self, product: Product) -> Product:
        """Insert product or update existing product listing and price history atomically."""
        pass


class DiscoveredURLRepositoryInterface(BaseRepository[DiscoveredURL]):
    """Repository interface for Discovered URLs and Queue persistence."""

    @abstractmethod
    async def get_next_pending(
        self, site_id: str | None = None, limit: int = 10
    ) -> Sequence[DiscoveredURL]:
        """Fetch next pending batch of URLs for worker consumption."""
        pass

    @abstractmethod
    async def update_status(
        self, url_id: str, status: URLStatusEnum, error_msg: str | None = None
    ) -> bool:
        """Update URL execution state and attempt counter."""
        pass

    @abstractmethod
    async def bulk_add_urls(self, urls: Sequence[DiscoveredURL]) -> int:
        """Bulk insert discovered product URLs, ignoring duplicates."""
        pass


class CrawlHistoryRepositoryInterface(BaseRepository[CrawlJob]):
    """Repository interface for Crawl Jobs and Execution History."""

    @abstractmethod
    async def get_interrupted_jobs(self) -> Sequence[CrawlJob]:
        """Retrieve incomplete or interrupted crawl jobs for resumption."""
        pass

    @abstractmethod
    async def save_schedule(self, schedule: CrawlSchedule) -> CrawlSchedule:
        """Save or update a CrawlSchedule entity."""
        pass

    @abstractmethod
    async def get_due_schedules(self) -> Sequence[CrawlSchedule]:
        """Fetch active crawl schedules that are due for execution."""
        pass
