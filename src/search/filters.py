"""Filtering utilities for evaluating and filtering Product listings based on search criteria."""

from src.domain.models.product import Product
from src.search.models import SearchFilters


def matches_brand(product: Product, brands: list[str] | None) -> bool:
    """Check if the product matches the brand filter criteria.

    Args:
        product: The Product entity.
        brands: List of permitted brand names.

    Returns:
        True if matched or if filter is not specified.
    """
    if not brands:
        return True
    return product.brand in brands


def matches_price(product: Product, min_price: float | None, max_price: float | None) -> bool:
    """Check if the product falls within the price range filter.

    Args:
        product: The Product entity.
        min_price: Minimum allowable price.
        max_price: Maximum allowable price.

    Returns:
        True if matched or if limits are not specified.
    """
    if min_price is not None and product.current_price < min_price:
        return False
    if max_price is not None and product.current_price > max_price:
        return False
    return True


def matches_category(product: Product, category: str | None) -> bool:
    """Check if the product category matches.

    Args:
        product: The Product entity.
        category: The category string or CategoryEnum value.

    Returns:
        True if matched or if filter is not specified.
    """
    if not category:
        return True
    # category can be either a CategoryEnum object or string
    p_cat = product.category.value if hasattr(product.category, "value") else str(product.category)
    filter_cat = category.value if hasattr(category, "value") else str(category)
    return p_cat == filter_cat


def matches_availability(product: Product, availability: bool | None) -> bool:
    """Check if the product availability matches.

    Args:
        product: The Product entity.
        availability: In-stock boolean flag or None.

    Returns:
        True if matched or if filter is not specified.
    """
    if availability is None:
        return True
    return product.is_in_stock == availability


def matches_store(product: Product, stores: list[str] | None) -> bool:
    """Check if the product was scraped from one of the store filter targets.

    Args:
        product: The Product entity.
        stores: List of allowed site ID/store strings.

    Returns:
        True if matched or if filter is not specified.
    """
    if not stores:
        return True
    return product.site_id in stores


def matches_filters(product: Product, filters: SearchFilters | None) -> bool:
    """Evaluate if a single product satisfies all active criteria in a SearchFilters schema.

    Args:
        product: The Product entity.
        filters: Active SearchFilters criteria.

    Returns:
        True if all filters match, False otherwise.
    """
    if not filters:
        return True

    return (
        matches_brand(product, filters.brand)
        and matches_price(product, filters.min_price, filters.max_price)
        and matches_category(product, filters.category)
        and matches_availability(product, filters.availability)
        and matches_store(product, filters.store)
    )


def filter_products(products: list[Product], filters: SearchFilters | None) -> list[Product]:
    """Filter a list of products using the criteria in a SearchFilters model.

    Args:
        products: The source list of Products.
        filters: Active filter criteria.

    Returns:
        A new filtered list of Products matching all criteria.
    """
    if not filters:
        return list(products)
    return [p for p in products if matches_filters(p, filters)]
