"""Unit tests for In-Memory Repositories (Product and URL)."""

import pytest

from src.domain.enums import CategoryEnum, CurrencyEnum, URLStatusEnum
from src.domain.models.product import Product
from src.domain.models.url import DiscoveredURL
from src.repositories.product import InMemoryProductRepository
from src.repositories.url import InMemoryURLRepository


@pytest.mark.asyncio
async def test_in_memory_product_repository() -> None:
    """Test InMemoryProductRepository CRUD, SKU, and listing operations."""
    repo = InMemoryProductRepository()

    product = Product(
        site_id="bestbuy_us",
        url="https://www.bestbuy.com/site/dell/123.p",
        sku="123",
        title="Dell Laptop",
        brand="Dell",
        model_name="XPS 13",
        category=CategoryEnum.LAPTOP,
        current_price=999.99,
        original_price=1099.99,
        currency=CurrencyEnum.USD,
        is_in_stock=True,
    )

    # Save Product
    saved = await repo.save(product)
    assert saved.id is not None

    # Get by ID
    fetched = await repo.get_by_id(saved.id)
    assert fetched is not None
    assert fetched.sku == "123"

    # Get by SKU
    fetched_sku = await repo.get_by_sku("123")
    assert fetched_sku is not None
    assert fetched_sku.id == saved.id

    # Get by URL
    fetched_url = await repo.get_by_url("https://www.bestbuy.com/site/dell/123.p")
    assert fetched_url is not None
    assert fetched_url.id == saved.id

    # List Products
    all_products = await repo.list_products()
    assert len(all_products) == 1

    # Update Product
    fetched.title = "Dell XPS Laptop"
    updated = await repo.update_product(fetched)
    assert updated.title == "Dell XPS Laptop"

    # Delete Product
    deleted = await repo.delete(saved.id)
    assert deleted is True
    assert len(await repo.list_products()) == 0


@pytest.mark.asyncio
async def test_in_memory_url_repository() -> None:
    """Test InMemoryURLRepository pending, attempts, and bulk operations."""
    repo = InMemoryURLRepository()

    url_item = DiscoveredURL(
        url="https://www.amazon.com/dp/B0CSB45V1D",
        site_id="amazon_us",
        category=CategoryEnum.MOBILE,
    )

    # Save URL
    saved = await repo.save(url_item)
    assert saved.id is not None
    assert saved.status == URLStatusEnum.PENDING

    # Get Pending URLs
    pending = await repo.get_next_pending(site_id="amazon_us", limit=5)
    assert len(pending) == 1
    assert pending[0].id == saved.id

    # Update Status to In Progress (should increment attempts)
    updated = await repo.update_status(saved.id, URLStatusEnum.IN_PROGRESS)
    assert updated is True
    fetched = await repo.get_by_id(saved.id)
    assert fetched is not None
    assert fetched.status == URLStatusEnum.IN_PROGRESS
    assert fetched.attempts == 1

    # Update Status with Error
    await repo.update_status(saved.id, URLStatusEnum.FAILED, error_msg="Timeout Error")
    fetched_failed = await repo.get_by_id(saved.id)
    assert fetched_failed is not None
    assert fetched_failed.status == URLStatusEnum.FAILED
    assert fetched_failed.last_error == "Timeout Error"

    # Bulk Add URLs (ignoring duplicates)
    url_list = [
        DiscoveredURL(url="https://www.amazon.com/dp/B0CSB45V1D", site_id="amazon_us"),  # Duplicate URL
        DiscoveredURL(url="https://www.amazon.com/dp/B0CSB45V2E", site_id="amazon_us"),  # New URL
    ]
    added = await repo.bulk_add_urls(url_list)
    assert added == 1
