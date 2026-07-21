"""Abstract Base Class for extracting domain Product models from raw web content."""

from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from src.domain.enums import CategoryEnum
from src.domain.models.product import Product


class BaseParser(ABC):
    """Abstract Base Class defining contract for raw HTML/JSON parser implementations."""

    @property
    @abstractmethod
    def site_id(self) -> str:
        """Site identifier matching the corresponding collector."""
        pass

    @property
    @abstractmethod
    def supported_category(self) -> CategoryEnum:
        """Supported product category."""
        pass

    @abstractmethod
    async def parse(
        self, html_content: str, url: str, raw_payload_id: str | None = None
    ) -> Product:
        """Parse raw HTML string and extract a normalized Product domain model.

        Args:
            html_content: Raw HTML document string.
            url: Canonical source page URL.
            raw_payload_id: Optional reference ID to raw storage document.

        Returns:
            Populated Product domain model.
        """
        pass

    def create_soup(self, html_content: str) -> BeautifulSoup:
        """Utility method to instantiate a BeautifulSoup object using lxml or html.parser."""
        return BeautifulSoup(html_content, "html.parser")
