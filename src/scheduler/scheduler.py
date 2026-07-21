"""Crawl Scheduler orchestrating recurring, incremental, and priority crawl runs."""

import asyncio
from datetime import UTC, datetime

from croniter import croniter

from src.core.exceptions import SchedulerError
from src.core.logging import get_logger
from src.domain.enums import CrawlStatusEnum, CrawlTypeEnum, PriorityEnum
from src.domain.models.crawl import CrawlJob, CrawlSchedule
from src.interfaces.repository import (
    CrawlHistoryRepositoryInterface,
    DiscoveredURLRepositoryInterface,
)
from src.scheduler.job_manager import JobManager

logger = get_logger(__name__)


class CrawlScheduler:
    """Orchestrates manual, scheduled, daily, weekly, incremental, and full crawl execution."""

    def __init__(
        self,
        repository: CrawlHistoryRepositoryInterface,
        url_repository: DiscoveredURLRepositoryInterface | None = None,
    ) -> None:
        self.repository = repository
        self.url_repository = url_repository
        self.job_manager = JobManager(repository)
        self._running = False
        self._loop_task: asyncio.Task[None] | None = None

    def calculate_next_run(self, cron_expr: str, base_time: datetime | None = None) -> datetime:
        """Calculate next scheduled execution datetime using cron expression."""
        now = base_time or datetime.now(UTC)
        try:
            iter_cron = croniter(cron_expr, now)
            next_ts = iter_cron.get_next(float)
            return datetime.fromtimestamp(next_ts, tz=UTC)
        except Exception as exc:
            raise SchedulerError(f"Invalid cron expression: {cron_expr}") from exc

    async def schedule_crawl(
        self,
        site_id: str,
        crawl_type: CrawlTypeEnum = CrawlTypeEnum.DAILY,
        cron_expr: str | None = None,
        priority: PriorityEnum = PriorityEnum.MEDIUM,
    ) -> CrawlSchedule:
        """Create and persist an automated CrawlSchedule."""
        if crawl_type == CrawlTypeEnum.DAILY and not cron_expr:
            cron_expr = "0 0 * * *"  # Midnight daily
        elif crawl_type == CrawlTypeEnum.WEEKLY and not cron_expr:
            cron_expr = "0 0 * * 0"  # Midnight Sunday weekly

        next_run = self.calculate_next_run(cron_expr) if cron_expr else None

        schedule = CrawlSchedule(
            site_id=site_id,
            crawl_type=crawl_type,
            cron_expression=cron_expr,
            priority=priority,
            next_run_at=next_run,
        )
        saved = await self.repository.save_schedule(schedule)
        logger.info(
            "Scheduled crawl job registered",
            site_id=site_id,
            crawl_type=crawl_type.value,
            next_run=str(next_run),
        )
        return saved

    async def trigger_manual_crawl(
        self,
        site_id: str,
        priority: PriorityEnum = PriorityEnum.HIGH,
        is_incremental: bool = False,
    ) -> CrawlJob:
        """Trigger an immediate manual or incremental crawl job."""
        crawl_type = CrawlTypeEnum.INCREMENTAL if is_incremental else CrawlTypeEnum.MANUAL
        job = await self.job_manager.create_job(
            site_id=site_id, crawl_type=crawl_type, priority=priority
        )
        logger.info("Triggered immediate manual crawl job", job_id=job.id, site_id=site_id)
        return job

    async def resume_interrupted_crawls(self) -> list[CrawlJob]:
        """Resume incomplete or interrupted crawl jobs."""
        interrupted_jobs = await self.job_manager.recover_interrupted_jobs()
        resumed_jobs: list[CrawlJob] = []

        for job in interrupted_jobs:
            logger.info("Resuming interrupted crawl job", job_id=job.id, site_id=job.site_id)
            job.status = CrawlStatusEnum.RUNNING
            job.error_summary = "Resumed after interruption"
            resumed = await self.repository.save(job)
            resumed_jobs.append(resumed)

        return resumed_jobs

    async def _scheduler_loop(self) -> None:
        """Background loop checking and triggering due scheduled crawls."""
        logger.info("Scheduler execution loop active")
        while self._running:
            try:
                due_schedules = await self.repository.get_due_schedules()
                for sched in due_schedules:
                    logger.info(
                        "Executing due scheduled crawl job",
                        schedule_id=sched.id,
                        site_id=sched.site_id,
                    )
                    # Create execution job
                    await self.job_manager.create_job(
                        site_id=sched.site_id,
                        crawl_type=sched.crawl_type,
                        priority=sched.priority,
                        schedule_id=sched.id,
                    )
                    # Update schedule timestamps
                    sched.last_run_at = datetime.now(UTC)
                    if sched.cron_expression:
                        sched.next_run_at = self.calculate_next_run(sched.cron_expression)
                    await self.repository.save_schedule(sched)

                await asyncio.sleep(10.0)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error in scheduler loop", error=str(exc))
                await asyncio.sleep(5.0)

    async def start(self) -> None:
        """Start background scheduler polling task."""
        if self._running:
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._scheduler_loop())
        logger.info("CrawlScheduler started successfully")

    async def stop(self) -> None:
        """Stop background scheduler task."""
        if not self._running:
            return
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.info("CrawlScheduler stopped")
