"""Unit tests for ProductSearchService orchestrations."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.enums import CategoryEnum
from src.domain.models.product import Product
from src.interfaces.repository import ProductRepositoryInterface
from src.search.models import SearchFilters, SearchRequest
from src.search.service import ProductSearchService


@pytest.fixture
def product_sample() -> Product:
    """Return a mock product."""
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


@pytest.mark.asyncio
async def test_search_service_sync_and_search(product_sample: Product) -> None:
    """Test sync_index_from_repository and search service coordination."""
    # Setup mock repository
    mock_repo = MagicMock(spec=ProductRepositoryInterface)
    mock_repo.list_products = AsyncMock(return_value=[product_sample])

    service = ProductSearchService(product_repository=mock_repo)

    # Sync
    indexed = await service.sync_index_from_repository()
    assert indexed == 1

    # Execute search request matching indexed item
    request = SearchRequest(
        query="Dell Laptop",
        page=1,
        page_size=10,
    )
    response = await service.search(request)
    assert response.total_results == 1
    assert response.results[0].product.id == "prod_123"
    assert response.results[0].matched_fields == ["title", "brand", "category"]


@pytest.mark.asyncio
async def test_search_service_filtering(product_sample: Product) -> None:
    """Test filters match evaluation in search service logic."""
    mock_repo = MagicMock(spec=ProductRepositoryInterface)
    mock_repo.list_products = AsyncMock(return_value=[product_sample])

    service = ProductSearchService(product_repository=mock_repo)
    await service.sync_index_from_repository()

    # Search with matching filters
    filters_matching = SearchFilters(brand=["Dell"], min_price=900.0, max_price=1100.0)
    request_matching = SearchRequest(query="Laptop", filters=filters_matching)
    response_matching = await service.search(request_matching)
    assert response_matching.total_results == 1

    # Search with non-matching filters
    filters_mismatch = SearchFilters(brand=["Samsung"])
    request_mismatch = SearchRequest(query="Laptop", filters=filters_mismatch)
    response_mismatch = await service.search(request_mismatch)
    assert response_mismatch.total_results == 0
