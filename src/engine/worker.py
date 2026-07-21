"""Worker Pool orchestrating concurrent pipeline execution consuming from AsyncURLQueue."""

import asyncio

from src.core.logging import get_logger
from src.core.metrics import ACTIVE_WORKERS_GAUGE
from src.engine.pipeline import ScrapePipeline
from src.engine.queue import AsyncURLQueue

logger = get_logger(__name__)


class WorkerPool:
    """Worker Pool running concurrent background async worker tasks processing URLQueue tasks."""

    def __init__(
        self,
        pipeline: ScrapePipeline,
        queue: AsyncURLQueue,
        concurrency: int = 5,
    ) -> None:
        self.pipeline = pipeline
        self.queue = queue
        self.concurrency = concurrency
        self._workers: list[asyncio.Task[None]] = []
        self._running = False

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker task loop pulling items from queue and running pipeline."""
        task_name = f"worker-{worker_id}"
        logger.info("Worker task started", worker_id=task_name)
        ACTIVE_WORKERS_GAUGE.inc()

        try:
            while self._running:
                try:
                    # Pull next URL from queue with timeout check
                    try:
                        item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                    except TimeoutError:
                        continue

                    logger.debug("Worker consumed URL task", worker=task_name, url=item.url)
                    try:
                        await self.pipeline.process_url(item, task_id=task_name)
                    except Exception as exc:
                        logger.error(
                            "Error processing URL item in worker",
                            worker=task_name,
                            url=item.url,
                            error=str(exc),
                        )
                    finally:
                        self.queue.task_done()

                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logger.error("Unexpected worker exception", worker=task_name, error=str(exc))

        finally:
            ACTIVE_WORKERS_GAUGE.dec()
            logger.info("Worker task stopped", worker_id=task_name)

    async def start(self) -> None:
        """Spawn worker task pool."""
        if self._running:
            return

        self._running = True
        logger.info("Starting WorkerPool", concurrency=self.concurrency)
        for i in range(self.concurrency):
            task = asyncio.create_task(self._worker_loop(i))
            self._workers.append(task)

    async def stop(self) -> None:
        """Cancel all worker tasks and shutdown pool."""
        if not self._running:
            return

        logger.info("Stopping WorkerPool")
        self._running = False
        for task in self._workers:
            task.cancel()

        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("WorkerPool stopped completely")
