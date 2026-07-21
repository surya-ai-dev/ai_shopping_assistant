"""Domain enumerations for product classification, crawl types, states, and priorities."""

from enum import StrEnum


class CategoryEnum(StrEnum):
    """Product domain category type."""

    LAPTOP = "laptop"
    MOBILE = "mobile"
    ACCESSORY = "accessory"
    GENERIC = "generic"


class CrawlTypeEnum(StrEnum):
    """Execution mode for crawl jobs."""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
    DAILY = "daily"
    WEEKLY = "weekly"
    INCREMENTAL = "incremental"
    FULL = "full"


class PriorityEnum(StrEnum):
    """Execution priority levels for crawl tasks and URLs."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class URLStatusEnum(StrEnum):
    """Processing state of a discovered URL in the URL repository/queue."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class CrawlStatusEnum(StrEnum):
    """Status of a CrawlJob or CrawlSchedule."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    INTERRUPTED = "interrupted"
    COMPLETED = "completed"
    FAILED = "failed"


class CurrencyEnum(StrEnum):
    """Currency standards."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    CAD = "CAD"
    AUD = "AUD"
