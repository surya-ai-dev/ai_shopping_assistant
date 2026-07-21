"""SQLAlchemy 2.0 ORM Mapped Models for Crawl Scheduler and Execution History."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base, TimestampMixin


class CrawlScheduleORM(Base, TimestampMixin):
    """Crawl automation schedules ORM model."""

    __tablename__ = "crawl_schedules"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    site_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    crawl_type: Mapped[str] = mapped_column(String(32), default="scheduled", nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    max_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_limit_override: Mapped[int | None] = mapped_column(Integer, nullable=True)

    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )


class CrawlJobORM(Base, TimestampMixin):
    """Crawl job execution run state ORM model."""

    __tablename__ = "crawl_jobs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    schedule_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    site_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    crawl_type: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)

    discovered_urls_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scraped_pages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_pages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extracted_products_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    checkpoint_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
