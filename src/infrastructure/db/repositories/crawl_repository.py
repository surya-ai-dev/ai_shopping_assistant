"""SQLAlchemy implementation of CrawlHistoryRepositoryInterface."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import RepositoryError
from src.core.logging import get_logger
from src.domain.enums import CrawlStatusEnum, CrawlTypeEnum, PriorityEnum
from src.domain.models.crawl import CrawlJob, CrawlSchedule
from src.infrastructure.db.models.crawl import CrawlJobORM, CrawlScheduleORM
from src.infrastructure.db.repositories.base import BaseSQLAlchemyRepository
from src.interfaces.repository import CrawlHistoryRepositoryInterface

logger = get_logger(__name__)


class CrawlRepository(BaseSQLAlchemyRepository[CrawlJob], CrawlHistoryRepositoryInterface):
    """Async SQLAlchemy Repository for Crawl Jobs, History, and Schedules."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, entity_id: str) -> CrawlJob | None:
        """Fetch CrawlJob by ID."""
        try:
            stmt = select(CrawlJobORM).where(CrawlJobORM.id == entity_id)
            res = await self.session.execute(stmt)
            orm = res.scalar_one_or_none()
            return self._job_to_domain(orm) if orm else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch CrawlJob {entity_id}", details={"error": str(exc)}
            ) from exc

    async def get_interrupted_jobs(self) -> Sequence[CrawlJob]:
        """Fetch incomplete or interrupted crawl jobs for resumption."""
        try:
            stmt = select(CrawlJobORM).where(
                CrawlJobORM.status.in_(
                    [CrawlStatusEnum.INTERRUPTED.value, CrawlStatusEnum.RUNNING.value]
                )
            )
            res = await self.session.execute(stmt)
            orms = res.scalars().all()
            return [self._job_to_domain(orm) for orm in orms]
        except Exception as exc:
            raise RepositoryError(
                "Failed to fetch interrupted crawl jobs", details={"error": str(exc)}
            ) from exc

    async def save(self, entity: CrawlJob) -> CrawlJob:
        """Save or update a CrawlJob run instance."""
        try:
            if entity.id:
                stmt = select(CrawlJobORM).where(CrawlJobORM.id == entity.id)
                res = await self.session.execute(stmt)
                orm = res.scalar_one_or_none()
            else:
                orm = None

            if orm:
                orm.status = entity.status.value
                orm.discovered_urls_count = entity.discovered_urls_count
                orm.scraped_pages_count = entity.scraped_pages_count
                orm.failed_pages_count = entity.failed_pages_count
                orm.extracted_products_count = entity.extracted_products_count
                orm.completed_at = entity.completed_at
                orm.error_summary = entity.error_summary
                orm.checkpoint_data = entity.checkpoint_data
                orm.updated_at = datetime.now(UTC)
            else:
                orm = CrawlJobORM(
                    schedule_id=entity.schedule_id,
                    site_id=entity.site_id,
                    crawl_type=entity.crawl_type.value,
                    priority=entity.priority.value,
                    status=entity.status.value,
                    discovered_urls_count=entity.discovered_urls_count,
                    scraped_pages_count=entity.scraped_pages_count,
                    failed_pages_count=entity.failed_pages_count,
                    extracted_products_count=entity.extracted_products_count,
                    started_at=entity.started_at or datetime.now(UTC),
                    completed_at=entity.completed_at,
                    error_summary=entity.error_summary,
                    checkpoint_data=entity.checkpoint_data,
                )
                self.session.add(orm)

            await self.session.flush()
            return self._job_to_domain(orm)
        except Exception as exc:
            raise RepositoryError("Failed to save CrawlJob", details={"error": str(exc)}) from exc

    async def save_schedule(self, schedule: CrawlSchedule) -> CrawlSchedule:
        """Save or update a CrawlSchedule."""
        try:
            if schedule.id:
                stmt = select(CrawlScheduleORM).where(CrawlScheduleORM.id == schedule.id)
                res = await self.session.execute(stmt)
                orm = res.scalar_one_or_none()
            else:
                orm = None

            if orm:
                orm.site_id = schedule.site_id
                orm.crawl_type = schedule.crawl_type.value
                orm.cron_expression = schedule.cron_expression
                orm.priority = schedule.priority.value
                orm.is_enabled = schedule.is_enabled
                orm.max_pages = schedule.max_pages
                orm.rate_limit_override = schedule.rate_limit_override
                orm.last_run_at = schedule.last_run_at
                orm.next_run_at = schedule.next_run_at
                orm.updated_at = datetime.now(UTC)
            else:
                orm = CrawlScheduleORM(
                    site_id=schedule.site_id,
                    crawl_type=schedule.crawl_type.value,
                    cron_expression=schedule.cron_expression,
                    priority=schedule.priority.value,
                    is_enabled=schedule.is_enabled,
                    max_pages=schedule.max_pages,
                    rate_limit_override=schedule.rate_limit_override,
                    last_run_at=schedule.last_run_at,
                    next_run_at=schedule.next_run_at,
                )
                self.session.add(orm)

            await self.session.flush()
            return CrawlSchedule(
                id=orm.id,
                site_id=orm.site_id,
                crawl_type=CrawlTypeEnum(orm.crawl_type),
                cron_expression=orm.cron_expression,
                priority=PriorityEnum(orm.priority),
                is_enabled=orm.is_enabled,
                max_pages=orm.max_pages,
                rate_limit_override=orm.rate_limit_override,
                last_run_at=orm.last_run_at,
                next_run_at=orm.next_run_at,
                created_at=orm.created_at,
            )
        except Exception as exc:
            raise RepositoryError(
                "Failed to save CrawlSchedule", details={"error": str(exc)}
            ) from exc

    async def get_due_schedules(self) -> Sequence[CrawlSchedule]:
        """Fetch active schedules that are due for execution."""
        try:
            now = datetime.now(UTC)
            stmt = select(CrawlScheduleORM).where(
                CrawlScheduleORM.is_enabled.is_(True),
                CrawlScheduleORM.next_run_at <= now,
            )
            res = await self.session.execute(stmt)
            orms = res.scalars().all()
            return [
                CrawlSchedule(
                    id=orm.id,
                    site_id=orm.site_id,
                    crawl_type=CrawlTypeEnum(orm.crawl_type),
                    cron_expression=orm.cron_expression,
                    priority=PriorityEnum(orm.priority),
                    is_enabled=orm.is_enabled,
                    max_pages=orm.max_pages,
                    rate_limit_override=orm.rate_limit_override,
                    last_run_at=orm.last_run_at,
                    next_run_at=orm.next_run_at,
                    created_at=orm.created_at,
                )
                for orm in orms
            ]
        except Exception as exc:
            raise RepositoryError(
                "Failed to fetch due crawl schedules", details={"error": str(exc)}
            ) from exc

    async def delete(self, entity_id: str) -> bool:
        """Delete CrawlJob by ID."""
        try:
            stmt = select(CrawlJobORM).where(CrawlJobORM.id == entity_id)
            res = await self.session.execute(stmt)
            orm = res.scalar_one_or_none()
            if orm:
                await self.session.delete(orm)
                await self.session.flush()
                return True
            return False
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete CrawlJob {entity_id}", details={"error": str(exc)}
            ) from exc

    def _job_to_domain(self, orm: CrawlJobORM) -> CrawlJob:
        """Map CrawlJobORM to domain model."""
        return CrawlJob(
            id=orm.id,
            schedule_id=orm.schedule_id,
            site_id=orm.site_id,
            crawl_type=CrawlTypeEnum(orm.crawl_type),
            priority=PriorityEnum(orm.priority),
            status=CrawlStatusEnum(orm.status),
            discovered_urls_count=orm.discovered_urls_count,
            scraped_pages_count=orm.scraped_pages_count,
            failed_pages_count=orm.failed_pages_count,
            extracted_products_count=orm.extracted_products_count,
            started_at=orm.started_at,
            completed_at=orm.completed_at,
            error_summary=orm.error_summary,
            checkpoint_data=orm.checkpoint_data or {},
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
