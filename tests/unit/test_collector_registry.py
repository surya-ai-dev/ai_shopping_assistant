"""Unit tests for Collector Registry and Plugin Auto-Discovery."""

import pytest

from src.core.exceptions import CollectorNotFoundError
from src.domain.enums import CategoryEnum
from src.engine.registry import CollectorRegistry
from src.interfaces.collector import BaseCollector
from src.interfaces.parser import BaseParser


class MockCollector(BaseCollector):
    site_id = "mock_site"
    supported_category = CategoryEnum.LAPTOP

    async def setup(self) -> None:
        pass

    async def teardown(self) -> None:
        pass

    async def health_check(self, page) -> bool:
        return True

    async def discover_urls(self, page, seed_url):
        return []

    async def fetch_page(self, page, url):
        return None


class MockParser(BaseParser):
    site_id = "mock_site"
    supported_category = CategoryEnum.LAPTOP

    async def parse(self, html_content: str, url: str, raw_payload_id=None):
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
