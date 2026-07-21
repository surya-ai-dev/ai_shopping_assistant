"""Domain model for Discovered Product URLs in the Queue/Repository."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain.enums import CategoryEnum, PriorityEnum, URLStatusEnum


class DiscoveredURL(BaseModel):
    """Product URL queue domain model."""

    id: str | None = Field(default=None, description="UUID primary key")
    url: str = Field(..., description="Target web page URL")
    site_id: str = Field(..., description="Target site identifier e.g. bestbuy")
    category: CategoryEnum = Field(default=CategoryEnum.GENERIC)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    status: URLStatusEnum = Field(default=URLStatusEnum.PENDING)

    attempts: int = Field(default=0, ge=0, description="Total scrape attempts")
    max_attempts: int = Field(default=3, ge=1, description="Maximum retry limit")
    last_error: str | None = Field(default=None, description="Last failure reason")

    depth: int = Field(default=0, ge=0, description="Crawl tree depth")
    parent_url: str | None = Field(default=None, description="Source referrer URL")
    job_id: str | None = Field(default=None, description="Associated CrawlJob ID")

    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
