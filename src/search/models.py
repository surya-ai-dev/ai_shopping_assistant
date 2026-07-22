"""Domain models representing search requests, filters, results, and responses."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from src.domain.enums import CategoryEnum
from src.domain.models.product import Product


class SortOption(StrEnum):
    """Sorting parameters supported by the search interface."""

    RELEVANCE = "relevance"
    PRICE_LOW_TO_HIGH = "price_low_to_high"
    PRICE_HIGH_TO_LOW = "price_high_to_low"
    NEWEST = "newest"


class SearchFilters(BaseModel):
    """Filter criteria to restrict query results."""

    brand: list[str] | None = Field(default=None, description="Filter products by list of brands")
    min_price: float | None = Field(default=None, ge=0.0, description="Minimum price limit")
    max_price: float | None = Field(default=None, ge=0.0, description="Maximum price limit")
    category: CategoryEnum | None = Field(default=None, description="Filter by product category classification")
    store: list[str] | None = Field(default=None, description="Filter by merchant store identifiers")
    availability: bool | None = Field(default=None, description="In-stock availability status filter")

    @model_validator(mode="after")
    def validate_price_range(self) -> "SearchFilters":
        """Validate that min_price does not exceed max_price if both are provided."""
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price cannot be greater than max_price")
        return self


class SearchRequest(BaseModel):
    """Query payload containing target terms, pagination parameters, and sort ordering options."""

    query: str = Field(..., min_length=1, description="Raw query search term string")
    page: int = Field(default=1, ge=1, description="Target page number index")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of results returned per page page")
    filters: SearchFilters | None = Field(default=None, description="Filter properties applied to search queries")
    sort_by: SortOption = Field(default=SortOption.RELEVANCE, description="Sorting parameter option")


class SearchResult(BaseModel):
    """Wrapper encapsulating a Product model alongside similarity score and matching highlights."""

    product: Product = Field(..., description="Target matched product entity")
    score: float = Field(..., ge=0.0, description="Relevance ranking score")
    matched_fields: list[str] = Field(default_factory=list, description="Fields where matches were detected")


class SearchResponse(BaseModel):
    """Response payload containing paginated search results list and metadata details."""

    total_results: int = Field(..., ge=0, description="Total matching documents count")
    page: int = Field(..., ge=1, description="Current response page index")
    page_size: int = Field(..., ge=1, description="Size limit returned on current page")
    total_pages: int = Field(..., ge=0, description="Calculated total pages count")
    has_next: bool = Field(..., description="Flag indicating next page existence")
    has_previous: bool = Field(..., description="Flag indicating previous page existence")
    results: list[SearchResult] = Field(default_factory=list, description="List of matched search results items")
