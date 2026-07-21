"""Domain models for Crawl Jobs, Schedules, and Execution Telemetry."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain.enums import CrawlStatusEnum, CrawlTypeEnum, PriorityEnum


class CrawlSchedule(BaseModel):
    """Configuration model for automated/recurring crawl jobs."""

    id: str | None = Field(default=None, description="Schedule UUID")
    site_id: str = Field(..., description="Target site identifier")
    crawl_type: CrawlTypeEnum = Field(default=CrawlTypeEnum.SCHEDULED)
    cron_expression: str | None = Field(default=None, description="Standard 5-field cron string")
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    is_enabled: bool = Field(default=True)

    max_pages: int | None = Field(default=None, ge=1)
    rate_limit_override: int | None = Field(default=None, ge=1)

    last_run_at: datetime | None = Field(default=None)
    next_run_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CrawlJob(BaseModel):
    """Model tracking execution of a crawl run."""

    id: str | None = Field(default=None, description="Job UUID")
    schedule_id: str | None = Field(default=None, description="Parent Schedule UUID if automated")
    site_id: str = Field(..., description="Target site identifier")
    crawl_type: CrawlTypeEnum = Field(default=CrawlTypeEnum.MANUAL)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    status: CrawlStatusEnum = Field(default=CrawlStatusEnum.PENDING)

    discovered_urls_count: int = Field(default=0, ge=0)
    scraped_pages_count: int = Field(default=0, ge=0)
    failed_pages_count: int = Field(default=0, ge=0)
    extracted_products_count: int = Field(default=0, ge=0)

    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    error_summary: str | None = Field(default=None)
    checkpoint_data: dict[str, Any] = Field(
        default_factory=dict, description="Interrupted job state"
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
