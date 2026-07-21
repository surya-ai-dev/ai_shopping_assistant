"""SQLAlchemy implementation of DiscoveredURLRepositoryInterface."""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import RepositoryError
from src.core.logging import get_logger
from src.domain.enums import CategoryEnum, PriorityEnum, URLStatusEnum
from src.domain.models.url import DiscoveredURL
from src.infrastructure.db.models.url import DiscoveredURLORM
from src.infrastructure.db.repositories.base import BaseSQLAlchemyRepository
from src.interfaces.repository import DiscoveredURLRepositoryInterface

logger = get_logger(__name__)


class DiscoveredURLRepository(
    BaseSQLAlchemyRepository[DiscoveredURL], DiscoveredURLRepositoryInterface
):
    """Async SQLAlchemy Discovered URL Repository for database queue operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, entity_id: str) -> DiscoveredURL | None:
        """Fetch URL entry by ID."""
        try:
            stmt = select(DiscoveredURLORM).where(DiscoveredURLORM.id == entity_id)
            res = await self.session.execute(stmt)
            orm = res.scalar_one_or_none()
            return self._to_domain(orm) if orm else None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to fetch URL {entity_id}", details={"error": str(exc)}
            ) from exc

    async def get_next_pending(
        self, site_id: str | None = None, limit: int = 10
    ) -> Sequence[DiscoveredURL]:
        """Fetch next batch of PENDING or RETRY status URLs ordered by priority and date."""
        try:
            stmt = select(DiscoveredURLORM).where(
                DiscoveredURLORM.status.in_(
                    [URLStatusEnum.PENDING.value, URLStatusEnum.RETRY.value]
                )
            )
            if site_id:
                stmt = stmt.where(DiscoveredURLORM.site_id == site_id)

            stmt = stmt.order_by(DiscoveredURLORM.created_at.asc()).limit(limit)
            result = await self.session.execute(stmt)
            orms = result.scalars().all()
            return [self._to_domain(orm) for orm in orms]
        except Exception as exc:
            raise RepositoryError(
                "Failed to fetch pending queue URLs", details={"error": str(exc)}
            ) from exc

    async def update_status(
        self, url_id: str, status: URLStatusEnum, error_msg: str | None = None
    ) -> bool:
        """Update URL status state and increment attempt counter."""
        try:
            stmt = select(DiscoveredURLORM).where(DiscoveredURLORM.id == url_id)
            res = await self.session.execute(stmt)
            orm = res.scalar_one_or_none()
            if not orm:
                return False

            orm.status = status.value
            orm.attempts += 1
            if error_msg:
                orm.last_error = error_msg
            orm.updated_at = datetime.now(UTC)

            await self.session.flush()
            return True
        except Exception as exc:
            raise RepositoryError(
                f"Failed to update URL status for {url_id}", details={"error": str(exc)}
            ) from exc

    async def bulk_add_urls(self, urls: Sequence[DiscoveredURL]) -> int:
        """Bulk insert discovered URLs into queue repository, ignoring duplicates."""
        if not urls:
            return 0

        try:
            inserted_count = 0
            for url_domain in urls:
                stmt = (
                    insert(DiscoveredURLORM)
                    .values(
                        url=url_domain.url,
                        site_id=url_domain.site_id,
                        category=url_domain.category.value,
                        priority=url_domain.priority.value,
                        status=url_domain.status.value,
                        attempts=url_domain.attempts,
                        max_attempts=url_domain.max_attempts,
                        depth=url_domain.depth,
                        parent_url=url_domain.parent_url,
                        job_id=url_domain.job_id,
                        metadata_json=url_domain.metadata,
                    )
                    .on_conflict_do_nothing(index_elements=["url"])
                )
                res = await self.session.execute(stmt)
                if isinstance(res, CursorResult) and res.rowcount > 0:
                    inserted_count += res.rowcount

            await self.session.flush()
            return inserted_count
        except Exception as exc:
            raise RepositoryError(
                "Failed to bulk insert discovered URLs", details={"error": str(exc)}
            ) from exc

    async def save(self, entity: DiscoveredURL) -> DiscoveredURL:
        """Save single DiscoveredURL entry."""
        await self.bulk_add_urls([entity])
        return entity

    async def delete(self, entity_id: str) -> bool:
        """Delete URL entry by ID."""
        try:
            stmt = select(DiscoveredURLORM).where(DiscoveredURLORM.id == entity_id)
            res = await self.session.execute(stmt)
            orm = res.scalar_one_or_none()
            if orm:
                await self.session.delete(orm)
                await self.session.flush()
                return True
            return False
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete URL {entity_id}", details={"error": str(exc)}
            ) from exc

    def _to_domain(self, orm: DiscoveredURLORM) -> DiscoveredURL:
        """Map ORM to domain model."""
        return DiscoveredURL(
            id=orm.id,
            url=orm.url,
            site_id=orm.site_id,
            category=CategoryEnum(orm.category),
            priority=PriorityEnum(orm.priority),
            status=URLStatusEnum(orm.status),
            attempts=orm.attempts,
            max_attempts=orm.max_attempts,
            last_error=orm.last_error,
            depth=orm.depth,
            parent_url=orm.parent_url,
            job_id=orm.job_id,
            metadata=orm.metadata_json or {},
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
