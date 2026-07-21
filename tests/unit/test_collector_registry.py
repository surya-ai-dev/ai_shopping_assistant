"""Unit tests for Collector Registry and Plugin Auto-Discovery."""

import pytest
from playwright.async_api import Page, Response

from src.core.exceptions import CollectorNotFoundError
from src.domain.enums import CategoryEnum
from src.domain.models.product import Product
from src.domain.models.url import DiscoveredURL
from src.engine.registry import CollectorRegistry
from src.interfaces.collector import BaseCollector
from src.interfaces.parser import BaseParser


class MockCollector(BaseCollector):
    @property
    def site_id(self) -> str:
        return "mock_site"

    @property
    def supported_category(self) -> CategoryEnum:
        return CategoryEnum.LAPTOP

    @property
    def supported_domains(self) -> list[str]:
        return ["mock.com"]

    async def setup(self) -> None:
        pass

    async def teardown(self) -> None:
        pass

    async def health_check(self, page: Page) -> bool:
        return True

    async def discover_urls(self, page: Page, seed_url: str) -> list[DiscoveredURL]:
        return []

    async def fetch_page(self, page: Page, url: str) -> Response | None:
        return None


class MockParser(BaseParser):
    @property
    def site_id(self) -> str:
        return "mock_site"

    @property
    def supported_category(self) -> CategoryEnum:
        return CategoryEnum.LAPTOP

    async def parse(self, html_content: str, url: str, raw_payload_id: str | None = None) -> Product:
        raise NotImplementedError()


def test_collector_registry_registration() -> None:
    """Test registering and retrieving collector/parser plugin classes."""
    CollectorRegistry.register("mock_site", MockCollector, MockParser)

    assert CollectorRegistry.get_collector("mock_site") == MockCollector
    assert CollectorRegistry.get_parser("mock_site") == MockParser
    assert "mock_site" in CollectorRegistry.list_sites()


def test_collector_registry_not_found() -> None:
    """Test getting unregistered site raises CollectorNotFoundError."""
    with pytest.raises(CollectorNotFoundError):
        CollectorRegistry.get_collector("non_existent_site")
