"""Async URL Queue supporting priority queues and database persistence backing."""

import asyncio

from src.core.logging import get_logger
from src.core.metrics import QUEUE_DEPTH_GAUGE
from src.domain.enums import PriorityEnum
from src.domain.models.url import DiscoveredURL
from src.interfaces.repository import DiscoveredURLRepositoryInterface

logger = get_logger(__name__)


class AsyncURLQueue:
    """Priority-aware in-memory & database backed URL Queue for decoupler workers."""

    def __init__(
        self, maxsize: int = 10000, repository: DiscoveredURLRepositoryInterface | None = None
    ) -> None:
        self.maxsize = maxsize
        self.repository = repository
        # Priority mapping: 0=HIGH, 1=MEDIUM, 2=LOW
        self._priority_queue: asyncio.PriorityQueue[tuple[int, float, DiscoveredURL]] = (
            asyncio.PriorityQueue(maxsize=maxsize)
        )
        self._counter = 0

    def _get_priority_weight(self, priority: PriorityEnum) -> int:
        """Map priority enum to integer sort index."""
        if priority == PriorityEnum.HIGH:
            return 0
        elif priority == PriorityEnum.MEDIUM:
            return 1
        return 2

    async def put(self, item: DiscoveredURL) -> None:
        """Put item into the queue."""
        weight = self._get_priority_weight(item.priority)
        self._counter += 1
        await self._priority_queue.put((weight, float(self._counter), item))

        # Update metrics
        QUEUE_DEPTH_GAUGE.labels(priority=item.priority.value).set(self._priority_queue.qsize())
        logger.debug("Enqueued URL task", url=item.url, priority=item.priority.value)

    async def get(self) -> DiscoveredURL:
        """Fetch highest priority pending URL from queue."""
        _, _, item = await self._priority_queue.get()
        QUEUE_DEPTH_GAUGE.labels(priority=item.priority.value).set(self._priority_queue.qsize())
        return item

    def task_done(self) -> None:
        """Mark enqueued task as completed."""
        self._priority_queue.task_done()

    def qsize(self) -> int:
        """Return current size of the queue."""
        return self._priority_queue.qsize()

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._priority_queue.empty()

    async def load_from_repository(self, site_id: str | None = None, batch_size: int = 50) -> int:
        """Load pending queue URLs from database repository into memory priority queue."""
        if not self.repository:
            return 0

        pending_urls = await self.repository.get_next_pending(site_id=site_id, limit=batch_size)
        loaded_count = 0
        for url_item in pending_urls:
            if not self._priority_queue.full():
                await self.put(url_item)
                loaded_count += 1

        logger.info("Loaded pending URLs from repository into queue", loaded_count=loaded_count)
        return loaded_count
