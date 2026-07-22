"""Ranking engine providing rule-based relevance scoring for Product search results."""

import re

from src.domain.models.product import Product


class ProductRanker:
    """Calculates relevance scores for Products against a search query using term weighting and availability boosts."""

    def __init__(
        self,
        title_weight: float = 2.0,
        brand_weight: float = 1.5,
        category_weight: float = 1.0,
        exact_title_boost: float = 5.0,
        in_stock_multiplier: float = 1.2,
    ) -> None:
        """Initialize the ranker with configurable scoring weights and boosts.

        Args:
            title_weight: Score points awarded for each query token matching the product title.
            brand_weight: Score points awarded for each query token matching the product brand.
            category_weight: Score points awarded for each query token matching the product category.
            exact_title_boost: Flat bonus points if the entire query string exactly matches the product title.
            in_stock_multiplier: Multiplicative boost applied to the final score if the product is in stock.
        """
        self.title_weight = title_weight
        self.brand_weight = brand_weight
        self.category_weight = category_weight
        self.exact_title_boost = exact_title_boost
        self.in_stock_multiplier = in_stock_multiplier

    def _tokenize(self, text: str) -> list[str]:
        """Split text into lowercased alphanumeric keywords."""
        if not text:
            return []
        return re.findall(r"\w+", text.lower())

    def calculate_score(self, product: Product, query: str) -> float:
        """Calculate the relevance score for a product against a search query.

        Args:
            product: The Product model instance.
            query: The search query string.

        Returns:
            The calculated floating-point relevance score.
        """
        query_cleaned = query.strip().lower()
        if not query_cleaned:
            return 0.0

        score = 0.0

        # 1. Exact Title Match Boost
        if product.title.strip().lower() == query_cleaned:
            score += self.exact_title_boost

        # Tokenize fields for keyword matching
        query_tokens = self._tokenize(query_cleaned)
        title_tokens = self._tokenize(product.title)
        brand_tokens = self._tokenize(product.brand)
        category_tokens = self._tokenize(product.category.value)

        # 2. Token Matching Scores
        for token in query_tokens:
            if token in title_tokens:
                score += self.title_weight
            if token in brand_tokens:
                score += self.brand_weight
            if token in category_tokens:
                score += self.category_weight

        # 3. Availability Boost
        if product.is_in_stock:
            score *= self.in_stock_multiplier

        return round(score, 4)

    def rank_products(self, products: list[Product], query: str) -> list[tuple[Product, float]]:
        """Score and sort a list of products in descending order of relevance.

        Args:
            products: List of Product instances.
            query: Search query string.

        Returns:
            A list of tuples containing the Product and its calculated score, sorted descending.
        """
        scored_products = [(p, self.calculate_score(p, query)) for p in products]
        # Sort by score descending
        scored_products.sort(key=lambda x: x[1], reverse=True)
        return scored_products
