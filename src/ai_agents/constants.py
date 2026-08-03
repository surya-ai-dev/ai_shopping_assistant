"""Constants used across the AI Agents platform."""

from typing import Final

# Supported categories
CATEGORY_LAPTOP: Final[str] = "laptop"
CATEGORY_MOBILE: Final[str] = "mobile"

# Supported intent classifications
INTENT_SEARCH_PRODUCT: Final[str] = "SEARCH_PRODUCT"
INTENT_COMPARE_PRODUCTS: Final[str] = "COMPARE_PRODUCTS"
INTENT_PRODUCT_DETAILS: Final[str] = "PRODUCT_DETAILS"
INTENT_PRICE_HISTORY: Final[str] = "PRICE_HISTORY"
INTENT_PRICE_DROP: Final[str] = "PRICE_DROP"
INTENT_REVIEW_SUMMARY: Final[str] = "REVIEW_SUMMARY"
INTENT_SHOPPING_ADVICE: Final[str] = "SHOPPING_ADVICE"
INTENT_GENERAL_GREETING: Final[str] = "GENERAL_GREETING"
INTENT_UNSUPPORTED: Final[str] = "UNSUPPORTED"

# Standard time-outs and retries
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
DEFAULT_MAX_RETRIES: Final[int] = 3
DEFAULT_LLM_TEMPERATURE: Final[float] = 0.0

# Logging fields
LOG_FIELD_REQUEST_ID: Final[str] = "request_id"
LOG_FIELD_CONVERSATION_ID: Final[str] = "conversation_id"
LOG_FIELD_TRACE_ID: Final[str] = "trace_id"
LOG_FIELD_COMPONENT: Final[str] = "component_name"
LOG_FIELD_DURATION: Final[str] = "execution_time_ms"
