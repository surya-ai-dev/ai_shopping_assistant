"""Crawl Pipeline orchestrating the full execution flow of crawling multi-site URLs."""

import asyncio
from collections.abc import Awaitable, Callable

from pydantic import BaseModel, Field

from src.core.logging import get_logger
from src.domain.enums import URLStatusEnum
from src.domain.models.product import Product
from src.domain.models.url import DiscoveredURL
from src.engine.pipeline import ScrapePipeline
from src.frontier.frontier import URLFrontier
from src.workers.pool import WorkerPool

logger = get_logger(__name__)


class CrawlerSettings(BaseModel):
    """Configuration schema for CrawlPipeline execution."""

    num_workers: int = Field(default=3, ge=1, description="Number of concurrent crawl workers")
    check_interval: float = Field(default=0.5, ge=0.1, description="Queue check interval in seconds")
    timeout_seconds: float | None = Field(default=None, description="Timeout limit for crawl job")


class CrawlPipeline:
    """Orchestrates seed url scheduling, pool initialization, and monitoring loops."""

    def __init__(
        self,
        frontier: URLFrontier,
        scrape_pipeline: ScrapePipeline,
        settings: CrawlerSettings | None = None,
        before_request_hook: Callable[[str], Awaitable[None]] | None = None,
        after_request_hook: Callable[[str, int], Awaitable[None]] | None = None,
        on_save_hook: Callable[[Product], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize CrawlPipeline with configuration settings and execution triggers.

        Args:
            frontier: URLFrontier to manage the priority queue and retry states.
            scrape_pipeline: Underlying multi-stage parser engine pipeline.
            settings: Configured CrawlerSettings parameters or None.
            before_request_hook: Optional hook callback invoked before fetching.
            after_request_hook: Optional hook callback invoked after fetching.
            on_save_hook: Optional hook callback invoked after database upsert.
        """
        self.frontier = frontier
        self.scrape_pipeline = scrape_pipeline
        self.settings = settings or CrawlerSettings()

        self.pool = WorkerPool(
            num_workers=self.settings.num_workers,
            frontier=self.frontier,
            pipeline=self.scrape_pipeline,
            before_request_hook=before_request_hook,
            after_request_hook=after_request_hook,
            on_save_hook=on_save_hook,
        )
        self._running = False

    async def run(self, seed_urls: list[DiscoveredURL]) -> dict[str, int]:
        """Execute complete concurrent crawl execution cycle for given seed list.

        Args:
            seed_urls: List of initial target URLs.

        Returns:
            Dictionary containing metrics aggregated from workers.
        """
        if self._running:
            logger.warning("CrawlPipeline is already executing, skipping run invocation")
            return self.pool.get_metrics()

        self._running = True
        logger.info("Initializing CrawlPipeline run", seed_urls_count=len(seed_urls))

        # Schedule input seed URL targets
        for url_item in seed_urls:
            await self.frontier.add_url(url_item)

        # Preload any pre-existing pending items for recovery
        await self.frontier.preload_from_repository()

        # Start pool workers
        self.pool.start()

        try:
            # Poll status until all queues and active workers are fully drained
            await self.wait_until_complete(
                check_interval=self.settings.check_interval,
                timeout=self.settings.timeout_seconds,
            )
        finally:
            # Assure clean worker release under error states
            await self.pool.stop()
            self._running = False

        metrics = self.pool.get_metrics()
        logger.info("CrawlPipeline execution finished", metrics=metrics)
        return metrics

    async def wait_until_complete(
        self, check_interval: float = 0.5, timeout: float | None = None
    ) -> None:
        """Block loop execution until priority queue is empty and active states reach zero.

        Args:
            check_interval: Polling frequency in seconds.
            timeout: Maximum allowed execution period.
        """
        start_time = asyncio.get_event_loop().time()
        while self._running:
            # Queue emptiness
            queue_empty = self.frontier.queue.empty()

            # Repository pending checks
            pending_batch = await self.frontier.url_repository.get_next_pending(limit=1)

            # In progress counts tracking
            in_progress_count = 0
            if hasattr(self.frontier.url_repository, "_urls"):
                in_progress_count = sum(
                    1
                    for u in self.frontier.url_repository._urls.values()
                    if u.status == URLStatusEnum.IN_PROGRESS
                )

            # Drained termination check
            if queue_empty and in_progress_count == 0 and len(pending_batch) == 0:
                logger.info("Frontier queue and active workers fully drained")
                break

            # Timeout check
            elapsed = asyncio.get_event_loop().time() - start_time
            if timeout is not None and elapsed > timeout:
                logger.warning("CrawlPipeline run timed out", elapsed_seconds=elapsed)
                break

            await asyncio.sleep(check_interval)
