"""Worker Pool managing lifecycle and lifecycle actions for multiple concurrent CrawlWorkers."""

import asyncio
from collections.abc import Awaitable, Callable

from src.core.logging import get_logger
from src.domain.models.product import Product
from src.engine.pipeline import ScrapePipeline
from src.frontier.frontier import URLFrontier
from src.workers.worker import CrawlWorker

logger = get_logger(__name__)


class WorkerPool:
    """Manages active concurrent workers, lifecycle start/stop, and metrics collection."""

    def __init__(
        self,
        num_workers: int,
        frontier: URLFrontier,
        pipeline: ScrapePipeline,
        before_request_hook: Callable[[str], Awaitable[None]] | None = None,
        after_request_hook: Callable[[str, int], Awaitable[None]] | None = None,
        on_save_hook: Callable[[Product], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize WorkerPool with desired worker count and pipeline parameters.

        Args:
            num_workers: Number of concurrent workers to spawn.
            frontier: URLFrontier instance sharing tasks.
            pipeline: ScrapePipeline processing context.
            before_request_hook: Pre-request execution hook.
            after_request_hook: Post-request execution hook.
            on_save_hook: Post-save database hook.
        """
        self.num_workers = num_workers
        self.frontier = frontier
        self.pipeline = pipeline
        self.before_request_hook = before_request_hook
        self.after_request_hook = after_request_hook
        self.on_save_hook = on_save_hook

        self.workers: list[CrawlWorker] = []
        self._active = False
        self._accumulated_metrics = {"processed": 0, "success": 0, "failed": 0, "retries": 0}

    def start(self) -> None:
        """Instantiate and start background execution loops for pool workers."""
        if self._active:
            logger.warning("WorkerPool is already active, skipping start")
            return

        self._active = True
        self.workers = []
        for i in range(self.num_workers):
            worker_id = f"worker_{i}"
            worker = CrawlWorker(
                worker_id=worker_id,
                frontier=self.frontier,
                pipeline=self.pipeline,
                before_request_hook=self.before_request_hook,
                after_request_hook=self.after_request_hook,
                on_save_hook=self.on_save_hook,
            )
            worker.start()
            self.workers.append(worker)

        logger.info("WorkerPool started successfully", active_workers=self.num_workers)

    async def stop(self) -> None:
        """Gracefully stop and await cancellation of all running pool workers."""
        if not self._active:
            return

        self._active = False
        logger.info("Stopping all workers in pool", active_workers=len(self.workers))
        stop_tasks = [worker.stop() for worker in self.workers]
        await asyncio.gather(*stop_tasks, return_exceptions=True)

        # Accumulate metrics before discarding worker instances
        for w in self.workers:
            self._accumulated_metrics["processed"] += w.processed_count
            self._accumulated_metrics["success"] += w.success_count
            self._accumulated_metrics["failed"] += w.fail_count
            self._accumulated_metrics["retries"] += w.retry_count

        self.workers = []
        logger.info("WorkerPool stopped completely")

    def get_metrics(self) -> dict[str, int]:
        """Aggregate scrape metrics across all active and completed pool workers.

        Returns:
            Dictionary containing processed, success, fail, and retry totals.
        """
        metrics = dict(self._accumulated_metrics)
        for w in self.workers:
            metrics["processed"] += w.processed_count
            metrics["success"] += w.success_count
            metrics["failed"] += w.fail_count
            metrics["retries"] += w.retry_count
        return metrics
