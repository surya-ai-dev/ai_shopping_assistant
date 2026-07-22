"""Search Service orchestrating product keyword searches, filters, sorting, and pagination."""

import math

from src.core.logging import get_logger
from src.domain.models.product import Product
from src.interfaces.repository import ProductRepositoryInterface
from src.search.index import ProductSearchIndex
from src.search.models import SearchRequest, SearchResponse, SearchResult, SortOption
from src.search.ranking import ProductRanker

logger = get_logger(__name__)


class ProductSearchService:
    """Service class coordinating search indexes, scoring algorithms, and pagination configurations."""

    def __init__(
        self,
        product_repository: ProductRepositoryInterface,
        search_index: ProductSearchIndex | None = None,
        ranker: ProductRanker | None = None,
    ) -> None:
        """Initialize the search service with dependencies.

        Args:
            product_repository: The abstract Product database repository.
            search_index: Custom search index instance or None.
            ranker: Custom ranker utility or None.
        """
        self.product_repository = product_repository
        self.search_index = search_index or ProductSearchIndex()
        self.ranker = ranker or ProductRanker()

    async def index_product(self, product: Product) -> None:
        """Index or update a single product's inverted index.

        Args:
            product: Product model instance.
        """
        try:
            await self.search_index.update_product(product)
        except Exception as exc:
            logger.error("Failed to index product", product_id=product.id, error=str(exc))

    async def deindex_product(self, product_id: str) -> None:
        """Deindex a product from search index.

        Args:
            product_id: UUID of the target product.
        """
        await self.search_index.remove_product(product_id)

    async def sync_index_from_repository(self) -> int:
        """Load all products from repository store to populate search indexes.

        Returns:
            Number of successfully indexed items.
        """
        logger.info("Initializing search index synchronization from repository")
        products = []
        if hasattr(self.product_repository, "list_products"):
            # Execute list lookup from in-memory or PostgreSQL db
            products = await self.product_repository.list_products()

        indexed_count = 0
        for prod in products:
            try:
                await self.search_index.update_product(prod)
                indexed_count += 1
            except Exception as exc:
                logger.warning("Skipped indexing product during sync", product_id=prod.id, error=str(exc))

        logger.info("Finished search index synchronization", indexed_count=indexed_count)
        return indexed_count

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Perform query keyword search against indexed products, applying filters, sorting, and pagination.

        Args:
            request: SearchRequest payload.

        Returns:
            SearchResponse containing matching paginated results.
        """
        logger.debug("Received product search request", query=request.query, page=request.page)

        # 1. Query Keyword Matches from Index
        matched_products = await self.search_index.search_keywords(request.query)

        # 2. Apply Filters (if provided)
        filtered_products: list[Product] = []
        for p in matched_products:
            if request.filters:
                filters = request.filters
                if filters.brand and p.brand not in filters.brand:
                    continue
                if filters.min_price is not None and p.current_price < filters.min_price:
                    continue
                if filters.max_price is not None and p.current_price > filters.max_price:
                    continue
                if filters.category and p.category != filters.category:
                    continue
                if filters.store and p.site_id not in filters.store:
                    continue
                if filters.availability is not None and p.is_in_stock != filters.availability:
                    continue
            filtered_products.append(p)

        # 3. Calculate Scores & Populate SearchResult
        results: list[SearchResult] = []
        query_tokens = self.ranker._tokenize(request.query)

        for p in filtered_products:
            score = self.ranker.calculate_score(p, request.query)

            # Determine matched fields
            matched_fields = []
            title_tokens = self.ranker._tokenize(p.title)
            brand_tokens = self.ranker._tokenize(p.brand)
            category_tokens = self.ranker._tokenize(p.category.value)

            if any(t in title_tokens for t in query_tokens):
                matched_fields.append("title")
            if any(t in brand_tokens for t in query_tokens):
                matched_fields.append("brand")
            if any(t in category_tokens for t in query_tokens):
                matched_fields.append("category")

            results.append(
                SearchResult(
                    product=p,
                    score=score,
                    matched_fields=matched_fields,
                )
            )

        # 4. Sorting
        if request.sort_by == SortOption.RELEVANCE:
            results.sort(key=lambda x: x.score, reverse=True)
        elif request.sort_by == SortOption.PRICE_LOW_TO_HIGH:
            results.sort(key=lambda x: x.product.current_price)
        elif request.sort_by == SortOption.PRICE_HIGH_TO_LOW:
            results.sort(key=lambda x: x.product.current_price, reverse=True)
        elif request.sort_by == SortOption.NEWEST:
            results.sort(key=lambda x: x.product.created_at, reverse=True)

        # 5. Pagination
        total_results = len(results)
        page_size = request.page_size
        total_pages = math.ceil(total_results / page_size) if total_results > 0 else 0

        start_idx = (request.page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = results[start_idx:end_idx]

        has_next = request.page < total_pages
        has_previous = request.page > 1

        return SearchResponse(
            total_results=total_results,
            page=request.page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            results=paginated_results,
        )
