"""Unit tests for ProductRanker scoring and sorting algorithms."""

import pytest

from src.domain.enums import CategoryEnum
from src.domain.models.product import Product
from src.search.ranking import ProductRanker


@pytest.fixture
def ranker() -> ProductRanker:
    """Return a ProductRanker instance."""
    return ProductRanker()


@pytest.fixture
def products_list() -> list[Product]:
    """Return a mock product list."""
    return [
        Product(
            id="p1",
            site_id="bestbuy_us",
            url="https://www.bestbuy.com/site/dell/1.p",
            title="Dell XPS Laptop",
            brand="Dell",
            model_name="XPS 13",
            category=CategoryEnum.LAPTOP,
            current_price=1000.0,
            is_in_stock=True,
        ),
        Product(
            id="p2",
            site_id="bestbuy_us",
            url="https://www.bestbuy.com/site/dell/2.p",
            title="Dell Inspiron",
            brand="Dell",
            model_name="Inspiron 15",
            category=CategoryEnum.LAPTOP,
            current_price=600.0,
            is_in_stock=False,
        ),
    ]


def test_ranking_relevance_calculation(ranker: ProductRanker, products_list: list[Product]) -> None:
    """Test calculate_score returns custom scoring weights and boosts."""
    p_in_stock = products_list[0]
    p_out_of_stock = products_list[1]

    # Exact title match score check:
    # Query exact title: "Dell XPS Laptop" -> exact_title_boost=5.0
    # Plus tokens matched:
    # "Dell" -> matches title & brand -> title_weight(2.0) + brand_weight(1.5) = 3.5
    # "XPS" -> matches title -> title_weight(2.0) = 2.0
    # "Laptop" -> matches title & category -> title_weight(2.0) + category_weight(1.0) = 3.0
    # Total pre-boost = 5.0 + 3.5 + 2.0 + 3.0 = 13.5
    # Since product is in stock: score = 13.5 * 1.2 = 16.2
    score_exact = ranker.calculate_score(p_in_stock, "Dell XPS Laptop")
    assert score_exact == 16.2

    # Partial query match: "Dell Laptop"
    # "Dell" -> matches title & brand -> 3.5
    # "Laptop" -> matches title & category -> 3.0
    # Total = 6.5
    # In stock multiplier -> 6.5 * 1.2 = 7.8
    score_partial = ranker.calculate_score(p_in_stock, "Dell Laptop")
    assert score_partial == 7.8

    # Out of stock check: "Dell Laptop" on p2 (out of stock)
    # "Dell" -> matches title & brand -> 3.5
    # "Laptop" -> matches category -> 1.0 (no "Laptop" in "Dell Inspiron" title)
    # Total = 4.5
    # Out of stock -> multiplier is NOT applied -> score = 4.5
    score_out_of_stock = ranker.calculate_score(p_out_of_stock, "Dell Laptop")
    assert score_out_of_stock == 4.5


def test_rank_products(ranker: ProductRanker, products_list: list[Product]) -> None:
    """Test rank_products sorts candidates by score descending."""
    ranked = ranker.rank_products(products_list, "Dell Laptop")
    assert len(ranked) == 2
    assert ranked[0][0].id == "p1"  # XPS has higher score
    assert ranked[1][0].id == "p2"
