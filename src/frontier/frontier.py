"""URL Frontier managing crawling queues, duplicates, and URL retry cycles."""

from datetime import UTC, datetime

from src.core.logging import get_logger
from src.domain.enums import URLStatusEnum
from src.domain.models.url import DiscoveredURL
from src.frontier.queue import PriorityQueue
from src.interfaces.repository import DiscoveredURLRepositoryInterface

logger = get_logger(__name__)


class URLFrontier:
    """Manages crawl scheduling state, retry thresholds, and duplicate url prevention."""

    def __init__(
        self,
        url_repository: DiscoveredURLRepositoryInterface,
        queue: PriorityQueue | None = None,
    ) -> None:
        """Initialize URLFrontier with queue and repository dependencies.

        Args:
            url_repository: Database or in-memory URL repository.
            queue: Custom priority queue instance or None.
        """
        self.url_repository = url_repository
        self.queue = queue or PriorityQueue()

    async def add_url(self, url_item: DiscoveredURL) -> bool:
        """Add a discovered URL item to the frontier, checking for duplicates.

        Args:
            url_item: DiscoveredURL to schedule.

        Returns:
            True if URL was newly added and scheduled, False if duplicate.
        """
        # Resolve from repository if it exists or save new one
        existing = None
        # We need to query by url string to prevent cross-run duplicates
        if hasattr(self.url_repository, "get_by_url"):
            # Check custom helper method on in-memory repo
            existing = await self.url_repository.get_by_url(url_item.url)

        if existing:
            # If completed, ignore. If failed but attempts < max, we can retry.
            logger.debug("URL already seen in repository", url=url_item.url, status=existing.status)
            return False

        # Persist URL to database in PENDING status
        url_item.status = URLStatusEnum.PENDING
        url_item.created_at = datetime.now(UTC)
        url_item.updated_at = datetime.now(UTC)
        saved = await self.url_repository.save(url_item)

        # Enqueue in priority queue
        await self.queue.put(saved)
        return True

    async def get_next_url(self) -> DiscoveredURL:
        """Fetch the next scheduled URL from the priority queue, blocking if empty.

        Returns:
            DiscoveredURL to process.
        """
        return await self.queue.get()

    async def mark_pending(self, url_item: DiscoveredURL) -> None:
        """Mark a URL status as pending and save to repository.

        Args:
            url_item: DiscoveredURL item.
        """
        url_item.status = URLStatusEnum.PENDING
        url_item.updated_at = datetime.now(UTC)
        await self.url_repository.save(url_item)
        await self.queue.put(url_item)

    async def mark_processing(self, url_id: str) -> None:
        """Mark URL state as in_progress inside the repository.

        Args:
            url_id: URL primary key.
        """
        await self.url_repository.update_status(url_id, URLStatusEnum.IN_PROGRESS)

    async def mark_completed(self, url_id: str) -> None:
        """Mark URL state as completed.

        Args:
            url_id: URL primary key.
        """
        await self.url_repository.update_status(url_id, URLStatusEnum.COMPLETED)
        # Clear from duplicate tracking to allow potential re-scheduling in future crawl cycles
        url_item = await self.url_repository.get_by_id(url_id)
        if url_item:
            await self.queue.clear_duplicate_tracking(url_item.url)

    async def mark_failed(self, url_id: str, error_msg: str | None = None) -> None:
        """Mark URL state as failed.

        Args:
            url_id: URL primary key.
            error_msg: Optional traceback description.
        """
        await self.url_repository.update_status(url_id, URLStatusEnum.FAILED, error_msg=error_msg)
        url_item = await self.url_repository.get_by_id(url_id)
        if url_item:
            await self.queue.clear_duplicate_tracking(url_item.url)

    async def retry_failed(self, url_item: DiscoveredURL, error_msg: str | None = None) -> bool:
        """Assess and execute retry logic for a failed URL.

        If attempts < max_attempts, update status to RETRY and enqueue back to the priority queue.
        Otherwise mark as FAILED.

        Args:
            url_item: Target DiscoveredURL.
            error_msg: Failure message.

        Returns:
            True if scheduled for retry, False if retry limit reached.
        """
        url_item.attempts += 1
        if url_item.attempts < url_item.max_attempts:
            url_item.status = URLStatusEnum.RETRY
            url_item.last_error = error_msg
            url_item.updated_at = datetime.now(UTC)
            await self.url_repository.save(url_item)
            await self.queue.put(url_item)
            logger.info(
                "Scheduled URL retry",
                url=url_item.url,
                attempt=url_item.attempts,
                max=url_item.max_attempts,
            )
            return True
        else:
            url_item.status = URLStatusEnum.FAILED
            url_item.last_error = error_msg or "Max attempts reached"
            url_item.updated_at = datetime.now(UTC)
            await self.url_repository.save(url_item)
            await self.queue.clear_duplicate_tracking(url_item.url)
            logger.warning(
                "Max retry attempts exceeded for URL",
                url=url_item.url,
                attempts=url_item.attempts,
            )
            return False

    async def preload_from_repository(self, site_id: str | None = None, limit: int = 100) -> int:
        """Preload pending/retry URLs from database/repository state into queue for recovery.

        Args:
            site_id: Filter by site ID.
            limit: Maximum items to load.

        Returns:
            Count of loaded items.
        """
        pending_items = await self.url_repository.get_next_pending(site_id=site_id, limit=limit)
        loaded = 0
        for item in pending_items:
            queued = await self.queue.put(item)
            if queued:
                loaded += 1
        logger.info("Preloaded URLs from repository to frontier queue", count=loaded)
        return loaded
