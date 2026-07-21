"""Abstract Base Class for site-specific page collectors."""

from abc import ABC, abstractmethod

from playwright.async_api import Page, Response

from src.core.request_manager import RequestManager
from src.domain.enums import CategoryEnum
from src.domain.models.url import DiscoveredURL


class BaseCollector(ABC):
    """Abstract Base Class defining the contract for all website collectors.

    Every website collector subclass must implement `site_id`, `supported_category`,
    `discover_urls()`, and `fetch_page()`.
    """

    def __init__(self, request_manager: RequestManager | None = None) -> None:
        self.request_manager = request_manager or RequestManager()

    @property
    @abstractmethod
    def site_id(self) -> str:
        """Unique identifier string for the site collector (e.g., 'amazon_us')."""
        pass

    @property
    @abstractmethod
    def supported_category(self) -> CategoryEnum:
        """Category type supported by this collector."""
        pass

    @abstractmethod
    async def setup(self) -> None:
        """Lifecycle hook executed prior to starting collection tasks."""
        pass

    @abstractmethod
    async def teardown(self) -> None:
        """Lifecycle hook executed upon completion of collection tasks."""
        pass

    @abstractmethod
    async def health_check(self, page: Page) -> bool:
        """Verify target website accessibility and anti-bot challenge status."""
        pass

    @abstractmethod
    async def discover_urls(self, page: Page, seed_url: str) -> list[DiscoveredURL]:
        """Crawl list pages or sitemaps to discover product URLs.

        Args:
            page: Active Playwright page context.
            seed_url: Listing page or seed URL.

        Returns:
            List of DiscoveredURL instances.
        """
        pass

    @abstractmethod
    async def fetch_page(self, page: Page, url: str) -> Response | None:
        """Navigate Playwright page to product target URL via RequestManager.

        Args:
            page: Active Playwright page.
            url: Target product page URL.

        Returns:
            Playwright Response object or None.
        """
        pass
