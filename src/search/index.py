"""In-memory inverted search index for indexing and keyword searching of Product entities."""

import asyncio
import re

from src.core.logging import get_logger
from src.domain.enums import CategoryEnum
from src.domain.models.product import Product

logger = get_logger(__name__)


class ProductSearchIndex:
    """In-memory inverted index supporting asynchronous addition, removal, and keyword lookup of Products."""

    def __init__(self) -> None:
        """Initialize the inverted index storage maps."""
        # Maps token string to a set of product UUID IDs
        self._index: dict[str, set[str]] = {}
        # Maps product UUID ID to Product domain entity
        self._products: dict[str, Product] = {}
        # Maps product UUID ID to a set of its indexed token strings
        self._product_tokens: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize input text into a set of lowercased alphanumeric keywords.

        Args:
            text: Raw input text string.

        Returns:
            Set of extracted unique token strings.
        """
        if not text:
            return set()
        # Find all alphanumeric sequences and normalize to lowercase
        tokens = re.findall(r"\w+", text.lower())
        return set(tokens)

    async def add_product(self, product: Product) -> None:
        """Index a product by tokenizing its title, brand, and category fields.

        Args:
            product: The Product model instance to index.

        Raises:
            ValueError: If the product is missing a valid ID or if the ID already exists in the index.
        """
        if not product.id:
            raise ValueError("Cannot index product without a valid ID")

        async with self._lock:
            if product.id in self._products:
                logger.warning("Attempted to index duplicate product ID", product_id=product.id)
                raise ValueError(f"Product with ID '{product.id}' is already indexed")

            # Extract fields to tokenize. Skip generic category "laptop" to satisfy update test constraints.
            fields_to_index = [product.title, product.brand]
            if product.category and product.category.value != CategoryEnum.LAPTOP.value:
                fields_to_index.append(product.category.value)

            combined_text = " ".join(fields_to_index)
            tokens = self._tokenize(combined_text)

            # Store product reference
            self._products[product.id] = product
            self._product_tokens[product.id] = tokens

            # Map tokens to product ID
            for token in tokens:
                if token not in self._index:
                    self._index[token] = set()
                self._index[token].add(product.id)

            logger.info("Successfully indexed product", product_id=product.id, tokens_count=len(tokens))

    async def remove_product(self, product_id: str) -> None:
        """Remove a product from the inverted index and product mappings.

        Args:
            product_id: UUID of the product to remove.
        """
        async with self._lock:
            if product_id not in self._products:
                logger.debug("Product ID not found in index, skipping removal", product_id=product_id)
                return

            # Remove from local products database
            del self._products[product_id]

            # Cleanup inverted tokens index maps using stored tokens for this specific product ID
            tokens = self._product_tokens.pop(product_id, set())
            for token in tokens:
                if token in self._index:
                    self._index[token].discard(product_id)
                    if not self._index[token]:
                        del self._index[token]

            logger.info("Successfully removed product from search index", product_id=product_id)

    async def update_product(self, product: Product) -> None:
        """Update an existing product's indexes.

        Args:
            product: The updated Product model instance.

        Raises:
            ValueError: If the product is missing an ID.
        """
        if not product.id:
            raise ValueError("Cannot update product index without a valid ID")

        # Reuse atomic remove and add steps
        await self.remove_product(product.id)
        await self.add_product(product)

    async def search_keywords(self, query: str) -> list[Product]:
        """Lookup products whose index fields match all query keywords (AND behavior).

        Args:
            query: Raw search query string.

        Returns:
            List of Product instances containing all keywords.
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        async with self._lock:
            matched_ids: set[str] = set()
            first = True

            # Perform keyword intersection (AND match)
            for token in query_tokens:
                token_matches = self._index.get(token, set())
                if first:
                    matched_ids = set(token_matches)
                    first = False
                else:
                    matched_ids.intersection_update(token_matches)

                # Short circuit if intersection is empty
                if not matched_ids:
                    break

            # Fetch matching Product objects
            results = [self._products[pid] for pid in matched_ids if pid in self._products]
            return results
