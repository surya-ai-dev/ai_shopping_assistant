"""In-memory implementation of ProductRepositoryInterface."""

import copy
import uuid

from src.domain.models.product import Product
from src.interfaces.repository import ProductRepositoryInterface


class InMemoryProductRepository(ProductRepositoryInterface):
    """In-memory Product Repository supporting CRUD and custom lookups."""

    def __init__(self) -> None:
        """Initialize product dict storage."""
        self._products: dict[str, Product] = {}

    async def get_by_id(self, entity_id: str) -> Product | None:
        """Fetch a product by its unique UUID ID."""
        return copy.deepcopy(self._products.get(entity_id))

    async def save(self, entity: Product) -> Product:
        """Create or update a product."""
        if not entity.id:
            entity.id = str(uuid.uuid4())
        self._products[entity.id] = copy.deepcopy(entity)
        return entity

    async def delete(self, entity_id: str) -> bool:
        """Delete a product by ID."""
        if entity_id in self._products:
            del self._products[entity_id]
            return True
        return False

    async def get_by_url(self, url: str) -> Product | None:
        """Retrieve product by canonical URL."""
        for prod in self._products.values():
            if prod.url == url:
                return copy.deepcopy(prod)
        return None

    async def get_by_fingerprint(self, hash_key: str) -> Product | None:
        """Retrieve product by fingerprint hash key."""
        for prod in self._products.values():
            if prod.fingerprint and prod.fingerprint.hash_key == hash_key:
                return copy.deepcopy(prod)
        return None

    async def upsert_product(self, product: Product) -> Product:
        """Insert product or update existing product listing."""
        existing = await self.get_by_url(product.url)
        if existing:
            product.id = existing.id
            # Merge price history
            price_history_map = {ph.timestamp: ph for ph in existing.price_history}
            for ph in product.price_history:
                price_history_map[ph.timestamp] = ph
            product.price_history = sorted(price_history_map.values(), key=lambda x: x.timestamp)
        return await self.save(product)

    async def update_product(self, product: Product) -> Product:
        """Explicit update product method."""
        if not product.id or product.id not in self._products:
            raise ValueError("Product must exist and have an ID to be updated")
        self._products[product.id] = copy.deepcopy(product)
        return product

    async def get_by_sku(self, sku: str) -> Product | None:
        """Retrieve product by store SKU or ASIN."""
        for prod in self._products.values():
            if prod.sku == sku:
                return copy.deepcopy(prod)
        return None

    async def list_products(self) -> list[Product]:
        """List all products stored in memory."""
        return [copy.deepcopy(p) for p in self._products.values()]
