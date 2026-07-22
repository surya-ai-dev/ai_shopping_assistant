"""Priority Queue implementation with FIFO and duplicate prevention."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.core.logging import get_logger
from src.domain.enums import PriorityEnum
from src.domain.models.url import DiscoveredURL

logger = get_logger(__name__)

# Map PriorityEnum to numeric values for sorting (lower value = higher priority)
PRIORITY_MAP = {
    PriorityEnum.HIGH: 0,
    PriorityEnum.MEDIUM: 1,
    PriorityEnum.LOW: 2,
}


@dataclass(order=True)
class QueueEntry:
    """Wrapper class to allow comparison in asyncio.PriorityQueue without comparing Pydantic models."""

    priority_score: int
    timestamp: float
    url: str = field(compare=False)
    item: DiscoveredURL = field(compare=False)


class PriorityQueue:
    """Thread-safe priority queue wrapping asyncio.PriorityQueue with duplicate prevention and FIFO support."""

    def __init__(self) -> None:
        """Initialize PriorityQueue and helper tracking sets."""
        self._queue: asyncio.PriorityQueue[QueueEntry] = asyncio.PriorityQueue()
        self._queued_urls: set[str] = set()
        self._lock = asyncio.Lock()

    async def put(self, item: DiscoveredURL) -> bool:
        """Enqueue a DiscoveredURL item if it is not already in the queue.

        Args:
            item: DiscoveredURL item to queue.

        Returns:
            True if queued, False if it was a duplicate.
        """
        async with self._lock:
            if item.url in self._queued_urls:
                logger.debug("URL already present in queue, skipping enqueue", url=item.url)
                return False

            self._queued_urls.add(item.url)
            priority_score = PRIORITY_MAP.get(item.priority, 1)
            # Use datetime timestamp for FIFO ordering of equal priority items
            timestamp = datetime.now(UTC).timestamp()
            entry = QueueEntry(
                priority_score=priority_score,
                timestamp=timestamp,
                url=item.url,
                item=item,
            )
            await self._queue.put(entry)
            logger.debug(
                "Enqueued URL",
                url=item.url,
                priority=item.priority,
                queue_size=self._queue.qsize(),
            )
            return True

        # Note: we need to allow type checkers to know that the lock block is the only path

    async def get(self) -> DiscoveredURL:
        """Retrieve the next highest priority item from the queue, blocking if empty.

        Returns:
            DiscoveredURL item.
        """
        entry = await self._queue.get()
        async with self._lock:
            if entry.url in self._queued_urls:
                self._queued_urls.remove(entry.url)
        return entry.item

    def empty(self) -> bool:
        """Check if queue is empty."""
        return self._queue.empty()

    def qsize(self) -> int:
        """Get the current number of items in the queue."""
        return self._queue.qsize()

    async def clear_duplicate_tracking(self, url: str) -> None:
        """Remove URL from queue tracking set to allow future re-queuing if needed.

        Args:
            url: Target URL string to clean from tracking.
        """
        async with self._lock:
            if url in self._queued_urls:
                self._queued_urls.remove(url)
