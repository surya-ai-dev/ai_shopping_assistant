"""Interfaces for future Vector Database and Embedding Service integrations."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from src.domain.models.product import Product


class VectorSearchResult(BaseModel):
    """Model representing a vector similarity search result."""

    product_id: str
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    payload: dict[str, Any] = Field(default_factory=dict)


class EmbeddingServiceInterface(ABC):
    """Abstract interface for text embedding generation services."""

    @abstractmethod
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate vector embedding representation for input text."""
        pass

    @abstractmethod
    async def generate_product_embedding(self, product: Product) -> list[float]:
        """Generate vector embedding representation for a Product entity."""
        pass


class VectorStorageInterface(ABC):
    """Abstract interface for Vector Database operations (e.g. Qdrant)."""

    @abstractmethod
    async def upsert_product_vector(
        self, product_id: str, vector: list[float], payload: dict[str, Any]
    ) -> bool:
        """Store or update product vector embedding and metadata payload."""
        pass

    @abstractmethod
    async def search_similar_products(
        self,
        query_vector: list[float],
        limit: int = 10,
        filter_criteria: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Perform similarity search using query vector."""
        pass

    @abstractmethod
    async def delete_vector(self, product_id: str) -> bool:
        """Remove product vector from index."""
        pass
