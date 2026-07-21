"""Domain models package."""

from src.domain.models.crawl import CrawlJob, CrawlSchedule
from src.domain.models.product import PriceHistory, Product, ProductFingerprint
from src.domain.models.quality import DataQualityReport
from src.domain.models.specs import GenericProductSpecs, LaptopSpecs, MobileSpecs
from src.domain.models.url import DiscoveredURL

__all__ = [
    "CrawlJob",
    "CrawlSchedule",
    "DataQualityReport",
    "DiscoveredURL",
    "GenericProductSpecs",
    "LaptopSpecs",
    "MobileSpecs",
    "PriceHistory",
    "Product",
    "ProductFingerprint",
]
