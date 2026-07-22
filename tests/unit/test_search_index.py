"""Unit tests for ProductSearchIndex class."""

import pytest

from src.domain.enums import CategoryEnum
from src.domain.models.product import Product
from src.search.index import ProductSearchIndex


@pytest.fixture
def product_sample() -> Product:
    """Return a mock laptop product."""
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
    )


@pytest.mark.asyncio
async def test_search_index_add_and_search(product_sample: Product) -> None:
    """Test indexing a product and looking it up using query keywords."""
    index = ProductSearchIndex()

    # Index product
    await index.add_product(product_sample)

    # Keyword search matching title
    results_title = await index.search_keywords("Dell Laptop")
    assert len(results_title) == 1
    assert results_title[0].id == "prod_123"

    # Keyword search matching brand
    results_brand = await index.search_keywords("dell")
    assert len(results_brand) == 1

    # Keyword search matching category
    results_cat = await index.search_keywords("laptop")
    assert len(results_cat) == 1

    # Search with query that does not match
    results_none = await index.search_keywords("samsung")
    assert len(results_none) == 0

    # Search with empty query
    results_empty = await index.search_keywords("")
    assert len(results_empty) == 0


@pytest.mark.asyncio
async def test_search_index_duplicate_prevention(product_sample: Product) -> None:
    """Test indexing the same product ID twice raises ValueError."""
    index = ProductSearchIndex()
    await index.add_product(product_sample)

    with pytest.raises(ValueError):
        await index.add_product(product_sample)


@pytest.mark.asyncio
async def test_search_index_remove_and_update(product_sample: Product) -> None:
    """Test removing and updating product indexing."""
    index = ProductSearchIndex()
    await index.add_product(product_sample)

    # Update product title
    product_sample.title = "Dell XPS 15 Chromebook"
    await index.update_product(product_sample)

    # Search using new keyword
    results_new = await index.search_keywords("Chromebook")
    assert len(results_new) == 1
    assert results_new[0].title == "Dell XPS 15 Chromebook"

    # Search using old keyword (should return no results)
    results_old = await index.search_keywords("Laptop")
    assert len(results_old) == 0

    # Remove product
    await index.remove_product(product_sample.id)
    results_after_remove = await index.search_keywords("Chromebook")
    assert len(results_after_remove) == 0
