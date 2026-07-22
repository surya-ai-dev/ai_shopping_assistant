"""Crawl Worker class pulling tasks from URLFrontier and executing processing pipeline."""

import asyncio
from collections.abc import Awaitable, Callable

from src.core.logging import get_logger
from src.domain.models.product import Product
from src.domain.models.url import DiscoveredURL
from src.engine.pipeline import ScrapePipeline
from src.frontier.frontier import URLFrontier

logger = get_logger(__name__)


class CrawlWorker:
    """Worker instance executing async crawl tasks."""

    def __init__(
        self,
        worker_id: str,
        frontier: URLFrontier,
        pipeline: ScrapePipeline,
        before_request_hook: Callable[[str], Awaitable[None]] | None = None,
        after_request_hook: Callable[[str, int], Awaitable[None]] | None = None,
        on_save_hook: Callable[[Product], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize CrawlWorker with dependencies.

        Args:
            worker_id: Unique string identifier for the worker.
            frontier: URLFrontier instance to pull URLs from.
            pipeline: ScrapePipeline instance to execute processing steps.
            before_request_hook: Async callback executed prior to page request.
            after_request_hook: Async callback executed after page request.
            on_save_hook: Async callback executed after DB persistence.
        """
        self.worker_id = worker_id
        self.frontier = frontier
        self.pipeline = pipeline
        self.before_request_hook = before_request_hook
        self.after_request_hook = after_request_hook
        self.on_save_hook = on_save_hook

        self._running = False
        self._current_task: asyncio.Task[None] | None = None

        # Worker-specific metrics
        self.processed_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.retry_count = 0

    async def run(self) -> None:
        """Run worker execution loop until cancelled or stopped."""
        self._running = True
        logger.info("Crawl worker started execution loop", worker_id=self.worker_id)
        while self._running:
            try:
                # Wait for next URL (blocks until queue has item or task gets cancelled)
                item = await self.frontier.get_next_url()
                logger.info(
                    "Worker pulled URL from frontier",
                    worker_id=self.worker_id,
                    url=item.url,
                )

                await self._process_item(item)

            except asyncio.CancelledError:
                logger.info("Worker execution loop cancelled", worker_id=self.worker_id)
                self._running = False
                break
            except Exception as exc:
                logger.error(
                    "Worker execution loop encountered unexpected error",
                    worker_id=self.worker_id,
                    error=str(exc),
                )
                await asyncio.sleep(1.0)

    async def _process_item(self, item: DiscoveredURL) -> None:
        """Execute processing pipeline steps for a target DiscoveredURL item.

        Args:
            item: DiscoveredURL item.
        """
        self.processed_count += 1
        if not item.id:
            logger.warning("DiscoveredURL item is missing id attribute", url=item.url)
            return

        # Mark URL state as processing
        await self.frontier.mark_processing(item.id)

        try:
            # Execute pre-request hook
            if self.before_request_hook:
                await self.before_request_hook(item.url)

            # Process URL through pipeline
            product = await self.pipeline.process_url(item, task_id=self.worker_id)

            # Execute post-request hook (simulate HTML size if product returns)
            if self.after_request_hook:
                # Approximate content size or mock
                html_size = len(product.title) if product else 0
                await self.after_request_hook(item.url, html_size)

            if product:
                # Execute on-save hook
                if self.on_save_hook:
                    await self.on_save_hook(product)

                # Mark completed successfully
                await self.frontier.mark_completed(item.id)
                self.success_count += 1
                logger.info(
                    "Worker successfully completed scrape task",
                    worker_id=self.worker_id,
                    url=item.url,
                )
            else:
                raise ValueError("Pipeline processing returned empty Product model")

        except Exception as exc:
            self.fail_count += 1
            logger.error(
                "Worker failed scrape task, assessing retry status",
                worker_id=self.worker_id,
                url=item.url,
                error=str(exc),
            )
            # Evaluate retries
            retried = await self.frontier.retry_failed(item, error_msg=str(exc))
            if retried:
                self.retry_count += 1
            else:
                await self.frontier.mark_failed(item.id, error_msg=str(exc))

    def start(self) -> None:
        """Start worker loop as background asyncio Task."""
        if self._current_task and not self._current_task.done():
            return
        self._current_task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        """Stop worker loop and await background task finalization."""
        self._running = False
        if self._current_task:
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                pass
            self._current_task = None
        logger.info("Crawl worker stopped", worker_id=self.worker_id)
