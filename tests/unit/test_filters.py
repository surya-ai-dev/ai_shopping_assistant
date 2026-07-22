"""Unit tests for search filters module."""

import pytest

from src.domain.enums import CategoryEnum
from src.domain.models.product import Product
from src.search.filters import (
    filter_products,
    matches_availability,
    matches_brand,
    matches_category,
    matches_filters,
    matches_price,
    matches_store,
)
from src.search.models import SearchFilters


@pytest.fixture
def product_fixture() -> Product:
    """Return a mock product for filtering test."""
    return Product(
        id="prod_123",
        site_id="bestbuy_us",
        url="https://www.bestbuy.com/site/dell/1.p",
        sku="1",
        title="Dell XPS 13 Laptop",
        brand="Dell",
        model_name="XPS 13",
        category=CategoryEnum.LAPTOP,
        current_price=999.99,
        is_in_stock=True,
    )


def test_matches_brand(product_fixture: Product) -> None:
    """Verify matches_brand matches product brand or returns True if filters are omitted."""
    assert matches_brand(product_fixture, ["Dell", "Samsung"]) is True
    assert matches_brand(product_fixture, ["Apple"]) is False
    assert matches_brand(product_fixture, []) is True
    assert matches_brand(product_fixture, None) is True


def test_matches_price(product_fixture: Product) -> None:
    """Verify matches_price respects upper/lower bounds."""
    assert matches_price(product_fixture, 900.0, 1100.0) is True
    assert matches_price(product_fixture, 1000.0, 1100.0) is False
    assert matches_price(product_fixture, 900.0, 950.0) is False
    assert matches_price(product_fixture, None, None) is True


def test_matches_category(product_fixture: Product) -> None:
    """Verify matches_category detects CategoryEnum values."""
    assert matches_category(product_fixture, CategoryEnum.LAPTOP) is True
    assert matches_category(product_fixture, CategoryEnum.MOBILE) is False
    assert matches_category(product_fixture, None) is True


def test_matches_availability(product_fixture: Product) -> None:
    """Verify matches_availability checks stock flags."""
    assert matches_availability(product_fixture, True) is True
    assert matches_availability(product_fixture, False) is False
    assert matches_availability(product_fixture, None) is True


def test_matches_store(product_fixture: Product) -> None:
    """Verify matches_store identifies site_id matching."""
    assert matches_store(product_fixture, ["bestbuy_us"]) is True
    assert matches_store(product_fixture, ["amazon_us"]) is False
    assert matches_store(product_fixture, None) is True


def test_matches_filters_and_filter_products(product_fixture: Product) -> None:
    """Verify filter_products correctly resolves list filtering evaluations."""
    filters = SearchFilters(brand=["Dell"], min_price=900.0, category=CategoryEnum.LAPTOP)
    assert matches_filters(product_fixture, filters) is True

    filters_fail = SearchFilters(brand=["Apple"])
    assert matches_filters(product_fixture, filters_fail) is False

    products = [product_fixture]
    assert len(filter_products(products, filters)) == 1
    assert len(filter_products(products, filters_fail)) == 0
    assert len(filter_products(products, None)) == 1
