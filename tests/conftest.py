"""Pytest shared test fixtures."""

import pytest

from src.core.request_manager import RequestManager
from src.domain.enums import CategoryEnum, CurrencyEnum
from src.domain.models.product import Product
from src.domain.models.specs import LaptopSpecs
from src.quality.assessor import DataQualityAssessor


@pytest.fixture
def sample_laptop_product() -> Product:
    """Fixture providing a valid Laptop product model."""
    return Product(
        site_id="bestbuy_us",
        url="https://www.bestbuy.com/site/laptop-12345.p",
        title="Dell XPS 15 Laptop - Intel i7 - 16GB RAM - 512GB SSD",
        brand="Dell",
        model_name="XPS 15 9530",
        category=CategoryEnum.LAPTOP,
        current_price=1499.99,
        original_price=1799.99,
        currency=CurrencyEnum.USD,
        is_in_stock=True,
        rating=4.5,
        review_count=120,
        image_urls=["https://images.bestbuy.com/laptop.jpg"],
        specs=LaptopSpecs(
            processor="Intel Core i7-13700H",
            ram_gb=16,
            storage_gb=512,
            screen_size_inches=15.6,
            operating_system="Windows 11 Home",
        ),
    )


@pytest.fixture
def quality_assessor() -> DataQualityAssessor:
    """Fixture providing DataQualityAssessor instance."""
    return DataQualityAssessor()


@pytest.fixture
def request_manager() -> RequestManager:
    """Fixture providing RequestManager instance."""
    return RequestManager(rate_per_minute=60, max_retries=2)
