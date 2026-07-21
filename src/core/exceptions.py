"""Core exception hierarchy for the Web Scraping Platform."""

from typing import Any


class ScraperError(Exception):
    """Base exception for all errors originating within the Web Scraping Platform."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(ScraperError):
    """Raised when environment variables or YAML configuration files are invalid or missing."""


class CollectorError(ScraperError):
    """Base exception for error conditions occurring during site collection execution."""


class CollectorNotFoundError(CollectorError):
    """Raised when a requested collector is not registered in the CollectorRegistry."""


class RequestManagerError(ScraperError):
    """Raised when request execution fails within the RequestManager."""


class RateLimitError(RequestManagerError):
    """Raised when rate limit bounds are breached or request is throttled."""


class MaxRetriesExceededError(RequestManagerError):
    """Raised when a fetch operation exceeds maximum retry attempts."""


class RequestTimeoutError(RequestManagerError):
    """Raised when a network or page rendering request times out."""


# Alias for backward compatibility
TimeoutError = RequestTimeoutError


class BrowserPoolError(ScraperError):
    """Base exception for Playwright Browser, Context, or Page pool failures."""


class ResourceExhaustedError(BrowserPoolError):
    """Raised when browser pool capacity is exhausted and timeout expires."""


class ParsingError(ScraperError):
    """Base exception for errors encountered during HTML/JSON parsing."""


class DataValidationError(ScraperError):
    """Raised when extracted product payload fails Pydantic schema validation."""


class DataQualityError(ScraperError):
    """Raised when data quality metrics fall below required thresholds."""


class DuplicateProductError(ScraperError):
    """Raised when a product listing is identified as a duplicate."""


class StorageError(ScraperError):
    """Base exception for raw storage or database persistence errors."""


class RawStorageError(StorageError):
    """Raised when saving or loading raw HTML/JSON payloads fails."""


class RepositoryError(StorageError):
    """Raised when database CRUD operations fail."""


class SchedulerError(ScraperError):
    """Raised when crawl scheduling or job resumption encounters an error."""


class VectorStorageError(ScraperError):
    """Raised when future vector database operations encounter an error."""
