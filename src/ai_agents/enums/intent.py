"""User query intent classification enums."""

from enum import StrEnum


class IntentEnum(StrEnum):
    """Supported intents for resolving user queries within the AI assistant."""

    SEARCH_PRODUCT = "SEARCH_PRODUCT"
    COMPARE_PRODUCTS = "COMPARE_PRODUCTS"
    PRODUCT_DETAILS = "PRODUCT_DETAILS"
    PRICE_HISTORY = "PRICE_HISTORY"
    PRICE_DROP = "PRICE_DROP"
    REVIEW_SUMMARY = "REVIEW_SUMMARY"
    SHOPPING_ADVICE = "SHOPPING_ADVICE"
    GENERAL_GREETING = "GENERAL_GREETING"
    UNSUPPORTED = "UNSUPPORTED"
    AVAILABILITY = "AVAILABILITY"
    FEATURE = "FEATURE"
    BRAND = "BRAND"
    BEST_PRODUCT = "BEST_PRODUCT"
