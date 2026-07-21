"""Interface for Raw HTML / Web Payload Storage."""

from abc import ABC, abstractmethod


class RawHTMLStorageInterface(ABC):
    """Abstract interface for storing and retrieving raw HTML web payloads."""

    @abstractmethod
    async def save_raw_html(self, url: str, site_id: str, html_content: str) -> str:
        """Store raw HTML content and return a unique storage key/id.

        Args:
            url: Page canonical URL.
            site_id: Origin site identifier.
            html_content: Raw HTML text content.

        Returns:
            Unique storage identifier string (e.g. hash or file path).
        """
        pass

    @abstractmethod
    async def get_raw_html(self, storage_id: str) -> str | None:
        """Retrieve stored raw HTML content by storage identifier string."""
        pass

    @abstractmethod
    async def exists(self, storage_id: str) -> bool:
        """Check if raw HTML content exists in storage."""
        pass
