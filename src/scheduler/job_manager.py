"""Job Manager tracking crawl run state, telemetry counters, and checkpoint recovery."""

from datetime import UTC, datetime
from typing import Any

from src.core.exceptions import SchedulerError
from src.core.logging import get_logger
from src.domain.enums import CrawlStatusEnum, CrawlTypeEnum, PriorityEnum
from src.domain.models.crawl import CrawlJob
from src.interfaces.repository import CrawlHistoryRepositoryInterface

logger = get_logger(__name__)


class JobManager:
    """Manages crawl job execution states, progress telemetry, and interrupted checkpoint recovery."""

    def __init__(self, repository: CrawlHistoryRepositoryInterface) -> None:
        self.repository = repository

    async def create_job(
        self,
        site_id: str,
        crawl_type: CrawlTypeEnum = CrawlTypeEnum.MANUAL,
        priority: PriorityEnum = PriorityEnum.MEDIUM,
        schedule_id: str | None = None,
    ) -> CrawlJob:
        """Create and persist a new CrawlJob instance."""
        job = CrawlJob(
            site_id=site_id,
            crawl_type=crawl_type,
            priority=priority,
            schedule_id=schedule_id,
            status=CrawlStatusEnum.RUNNING,
            started_at=datetime.now(UTC),
        )
        saved = await self.repository.save(job)
        logger.info(
            "Created new CrawlJob", job_id=saved.id, site_id=site_id, crawl_type=crawl_type.value
        )
        return saved

    async def update_checkpoint(
        self,
        job_id: str,
        discovered_urls: int = 0,
        scraped_pages: int = 0,
        failed_pages: int = 0,
        extracted_products: int = 0,
        checkpoint_data: dict[str, Any] | None = None,
    ) -> CrawlJob:
        """Update job progress telemetry and save checkpoint state for recovery."""
        job = await self.repository.get_by_id(job_id)
        if not job:
            raise SchedulerError(f"CrawlJob with id {job_id} not found")

        job.discovered_urls_count += discovered_urls
        job.scraped_pages_count += scraped_pages
        job.failed_pages_count += failed_pages
        job.extracted_products_count += extracted_products
        if checkpoint_data:
            job.checkpoint_data.update(checkpoint_data)

        saved = await self.repository.save(job)
        logger.debug(
            "Updated CrawlJob progress checkpoint", job_id=job_id, scraped=job.scraped_pages_count
        )
        return saved

    async def complete_job(
        self,
        job_id: str,
        status: CrawlStatusEnum = CrawlStatusEnum.COMPLETED,
        error_msg: str | None = None,
    ) -> CrawlJob:
        """Finalize job execution state."""
        job = await self.repository.get_by_id(job_id)
        if not job:
            raise SchedulerError(f"CrawlJob with id {job_id} not found")

        job.status = status
        job.completed_at = datetime.now(UTC)
        if error_msg:
            job.error_summary = error_msg

        saved = await self.repository.save(job)
        logger.info("Finalized CrawlJob state", job_id=job_id, status=status.value)
        return saved

    async def recover_interrupted_jobs(self) -> list[CrawlJob]:
        """Fetch incomplete or interrupted jobs to resume execution."""
        interrupted = await self.repository.get_interrupted_jobs()
        logger.info("Discovered interrupted jobs for resumption", count=len(interrupted))
        return list(interrupted)
