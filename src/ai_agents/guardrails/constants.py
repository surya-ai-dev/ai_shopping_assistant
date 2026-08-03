"""Constants and configuration settings for the AI Guardrails Layer."""

from typing import Final

# Supported categories for shopping guidance
SUPPORTED_CATEGORIES: Final[list[str]] = [
    "laptop",
    "mobile phone",
]

# Keyword lists for category matching (imported/re-declared for standalone capability)
LAPTOP_KEYWORDS: Final[list[str]] = [
    "laptop",
    "notebook",
    "ultrabook",
    "macbook",
    "chromebook",
]

MOBILE_KEYWORDS: Final[list[str]] = [
    "mobile",
    "phone",
    "smartphone",
    "iphone",
    "android",
    "galaxy",
    "pixel",
    "oneplus",
    "nothing phone",
    "redmi",
    "xiaomi",
    "vivo",
    "oppo",
    "motorola",
]

# Supported capabilities
SUPPORTED_CAPABILITIES: Final[list[str]] = [
    "compare products",
    "recommend products",
    "price comparison",
    "feature comparison",
    "shopping advice",
]

# Forbidden capabilities
FORBIDDEN_CAPABILITIES: Final[list[str]] = [
    "coding",
    "essay writing",
    "translation",
    "math",
    "general knowledge",
]

# Default conversation bounds
DEFAULT_MAX_TURNS: Final[int] = 20
DEFAULT_MAX_HISTORY_LENGTH: Final[int] = 4000
DEFAULT_MAX_CONVERSATION_AGE_SECONDS: Final[int] = 3600

# Professional tone guidelines
TONE_RULES: Final[list[str]] = [
    "Always maintain a professional, helpful, and polite tone.",
    "Only answer shopping-related queries about laptops and mobile phones.",
    "Do not provide code fragments, essays, translations, or general knowledge.",
    "Be objective and base advice on factual product features.",
]
