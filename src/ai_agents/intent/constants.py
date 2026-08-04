"""Constants and configuration registries for the AI Intent Classification Layer."""

from typing import Final

from src.ai_agents.enums.intent import IntentEnum

# Intent priorities (higher values resolve conflicts when multiple detectors match)
INTENT_PRIORITIES: Final[dict[IntentEnum, int]] = {
    IntentEnum.COMPARE_PRODUCTS: 100,
    IntentEnum.SHOPPING_ADVICE: 90,
    IntentEnum.SEARCH_PRODUCT: 80,
    IntentEnum.PRODUCT_DETAILS: 70,
    IntentEnum.PRICE_HISTORY: 60,
    IntentEnum.PRICE_DROP: 60,
    IntentEnum.FEATURE: 50,
    IntentEnum.AVAILABILITY: 40,
    IntentEnum.BRAND: 30,
    IntentEnum.BEST_PRODUCT: 20,
    IntentEnum.GENERAL_GREETING: 10,
    IntentEnum.UNSUPPORTED: 0,
}

# Confidence boundary thresholds
THRESHOLD_VERY_HIGH: Final[float] = 0.90
THRESHOLD_HIGH: Final[float] = 0.75
THRESHOLD_MEDIUM: Final[float] = 0.50

# Keyword lists for matching detectors
COMPARISON_KEYWORDS: Final[list[str]] = [
    "compare", "versus", "vs", "difference", "differ", "alternative",
    "better than", "compared to"
]

RECOMMENDATION_KEYWORDS: Final[list[str]] = [
    "recommend", "suggest", "advice", "what should i buy", "which is better",
    "help me choose", "shopping advice"
]

SEARCH_KEYWORDS: Final[list[str]] = [
    "find", "search", "show me", "looking for", "browse", "get me",
    "laptops under", "phones under", "list of"
]

DETAILS_KEYWORDS: Final[list[str]] = [
    "details", "specs", "specification", "info", "information", "features",
    "resolution", "weight", "dimensions", "ports", "warranty"
]

PRICE_KEYWORDS: Final[list[str]] = [
    "price", "cost", "history", "drop", "cheap", "expensive", "budget",
    "discount", "deal", "pricing", "how much"
]

AVAILABILITY_KEYWORDS: Final[list[str]] = [
    "available", "stock", "in stock", "buy", "delivery", "shipping",
    "purchase", "order", "where to buy"
]

FEATURE_KEYWORDS: Final[list[str]] = [
    "screen", "battery", "camera", "ram", "storage", "weight", "cpu",
    "gpu", "processor", "memory", "display", "color", "operating system"
]

BRAND_KEYWORDS: Final[list[str]] = [
    "apple", "samsung", "dell", "lenovo", "hp", "asus", "acer", "msi",
    "google", "oneplus", "xiaomi", "redmi", "oppo", "vivo", "motorola"
]

BEST_PRODUCT_KEYWORDS: Final[list[str]] = [
    "best", "top", "highest rated", "rank", "greatest", "premium"
]

GREETING_KEYWORDS: Final[list[str]] = [
    "hello", "hi", "hey", "greetings", "good morning", "good afternoon",
    "howdy", "sup"
]
