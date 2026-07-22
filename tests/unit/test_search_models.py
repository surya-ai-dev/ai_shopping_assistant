"""Unit tests for Search Domain Models and Pydantic validation rules."""

import pytest
from pydantic import ValidationError

from src.domain.enums import CategoryEnum, CurrencyEnum
from src.domain.models.product import Product
from src.search.models import SearchFilters, SearchRequest, SearchResponse, SearchResult, SortOption


def test_sort_option_enum() -> None:
    """Verify SortOption enum parameters."""
    assert SortOption.RELEVANCE == "relevance"
    assert SortOption.PRICE_LOW_TO_HIGH == "price_low_to_high"
    assert SortOption.PRICE_HIGH_TO_LOW == "price_high_to_low"
    assert SortOption.NEWEST == "newest"


def test_search_filters_validation() -> None:
    """Verify SearchFilters model validation constraints."""
    # Valid filter configurations
    filters = SearchFilters(
        brand=["Samsung", "Apple"],
        min_price=100.0,
        max_price=500.0,
        category=CategoryEnum.MOBILE,
        availability=True,
    )
    assert filters.brand == ["Samsung", "Apple"]
    assert filters.min_price == 100.0
    assert filters.max_price == 500.0
    assert filters.category == CategoryEnum.MOBILE
    assert filters.availability is True

    # Invalid min_price ge constraint validation
    with pytest.raises(ValidationError):
        SearchFilters(min_price=-10.0)

    # Invalid max_price range validation
    with pytest.raises(ValidationError):
        SearchFilters(min_price=200.0, max_price=100.0)


def test_search_request_validation() -> None:
    """Verify SearchRequest pagination and query parameters constraint checks."""
    request = SearchRequest(
        query="laptop",
        page=2,
        page_size=10,
        sort_by=SortOption.PRICE_LOW_TO_HIGH,
    )
    assert request.query == "laptop"
    assert request.page == 2
    assert request.page_size == 10
    assert request.sort_by == SortOption.PRICE_LOW_TO_HIGH

    # Empty query validation
    with pytest.raises(ValidationError):
        SearchRequest(query="")

    # Invalid page validation
    with pytest.raises(ValidationError):
        SearchRequest(query="laptop", page=0)

    # Invalid page_size limit validation
    with pytest.raises(ValidationError):
        SearchRequest(query="laptop", page_size=200)


def test_search_result_wrapping() -> None:
    """Verify SearchResult encapsulates Product domain model and scores."""
    product = Product(
        id="prod_123",
        site_id="bestbuy_us",
        url="https://www.bestbuy.com/site/dell/1.p",
        sku="1",
        title="Dell Laptop",
        brand="Dell",
        model_name="XPS 13",
        category=CategoryEnum.LAPTOP,
        current_price=999.99,
        currency=CurrencyEnum.USD,
    )
    result = SearchResult(product=product, score=4.5, matched_fields=["title"])
    assert result.product.id == "prod_123"
    assert result.score == 4.5
    assert result.matched_fields == ["title"]


def test_search_response_pagination_metadata() -> None:
    """Verify SearchResponse includes exact pagination metadata fields."""
    response = SearchResponse(
        total_results=2,
        page=1,
        page_size=20,
        total_pages=1,
        has_next=False,
        has_previous=False,
        results=[],
    )
    assert response.total_results == 2
    assert response.page == 1
    assert response.page_size == 20
    assert response.total_pages == 1
    assert response.has_next is False
    assert response.has_previous is False
