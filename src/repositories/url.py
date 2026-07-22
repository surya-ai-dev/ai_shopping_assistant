"""In-memory implementation of DiscoveredURLRepositoryInterface."""

import copy
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from src.domain.enums import URLStatusEnum
from src.domain.models.url import DiscoveredURL
from src.interfaces.repository import DiscoveredURLRepositoryInterface


class InMemoryURLRepository(DiscoveredURLRepositoryInterface):
    """In-memory URL Repository supporting crawler frontier operations."""

    def __init__(self) -> None:
        """Initialize URL dict storage."""
        self._urls: dict[str, DiscoveredURL] = {}

    async def get_by_id(self, entity_id: str) -> DiscoveredURL | None:
        """Fetch a URL by its unique UUID ID."""
        return copy.deepcopy(self._urls.get(entity_id))

    async def save(self, entity: DiscoveredURL) -> DiscoveredURL:
        """Create or update a URL."""
        if not entity.id:
            entity.id = str(uuid.uuid4())
        entity.updated_at = datetime.now(UTC)
        self._urls[entity.id] = copy.deepcopy(entity)
        return entity

    async def delete(self, entity_id: str) -> bool:
        """Delete a URL by ID."""
        if entity_id in self._urls:
            del self._urls[entity_id]
            return True
        return False

    async def get_by_url(self, url: str) -> DiscoveredURL | None:
        """Retrieve a URL by its canonical URL string."""
        for u in self._urls.values():
            if u.url == url:
                return copy.deepcopy(u)
        return None

    async def get_next_pending(
        self, site_id: str | None = None, limit: int = 10
    ) -> Sequence[DiscoveredURL]:
        """Fetch next pending/retry URLs for consumption."""
        pending = []
        for u in self._urls.values():
            if u.status in (URLStatusEnum.PENDING, URLStatusEnum.RETRY):
                if site_id is None or u.site_id == site_id:
                    pending.append(copy.deepcopy(u))
        pending.sort(key=lambda x: x.created_at)
        return pending[:limit]

    async def update_status(
        self, url_id: str, status: URLStatusEnum, error_msg: str | None = None
    ) -> bool:
        """Update URL execution state, attempt counter, and timestamps."""
        if url_id not in self._urls:
            return False
        url_item = self._urls[url_id]
        url_item.status = status
        url_item.updated_at = datetime.now(UTC)
        if error_msg:
            url_item.last_error = error_msg
        if status == URLStatusEnum.IN_PROGRESS:
            url_item.attempts += 1
        return True

    async def bulk_add_urls(self, urls: Sequence[DiscoveredURL]) -> int:
        """Bulk insert discovered URLs, ignoring duplicates."""
        added_count = 0
        for u in urls:
            # Check duplicate by URL string
            existing = await self.get_by_url(u.url)
            if not existing:
                await self.save(u)
                added_count += 1
        return added_count
