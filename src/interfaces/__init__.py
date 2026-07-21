"""Core interfaces and abstract protocols package."""

from src.interfaces.collector import BaseCollector
from src.interfaces.parser import BaseParser
from src.interfaces.raw_storage import RawHTMLStorageInterface
from src.interfaces.repository import (
    BaseRepository,
    CrawlHistoryRepositoryInterface,
    DiscoveredURLRepositoryInterface,
    ProductRepositoryInterface,
)
from src.interfaces.vector import (
    EmbeddingServiceInterface,
    VectorSearchResult,
    VectorStorageInterface,
)

__all__ = [
    "BaseCollector",
    "BaseParser",
    "BaseRepository",
    "CrawlHistoryRepositoryInterface",
    "DiscoveredURLRepositoryInterface",
    "EmbeddingServiceInterface",
    "ProductRepositoryInterface",
    "RawHTMLStorageInterface",
    "VectorSearchResult",
    "VectorStorageInterface",
]
