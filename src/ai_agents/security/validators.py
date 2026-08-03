"""Input validation rules for the security layer."""

import re
import unicodedata
from typing import Any, Protocol

from src.ai_agents.constants import LAPTOP_KEYWORDS, MOBILE_KEYWORDS


class SecurityValidator(Protocol):
    """Protocol defining the interface for security validators."""

    @property
    def name(self) -> str:
        """The name of the validator."""
        ...

    def validate(self, query: str, metadata: dict[str, Any] | None = None) -> tuple[bool, str | None]:
        """Validate the user query and request metadata.

        Args:
            query: The prompt/query string to validate.
            metadata: Context metadata dictionary.

        Returns:
            A tuple of (is_valid, error_message).
        """
        ...


class InputValidator:
    """Validator for basic input structure, length constraints, and unicode safety."""

    def __init__(self, min_length: int = 1, max_length: int = 4000) -> None:
        """Initialize the InputValidator.

        Args:
            min_length: Minimum allowed query length.
            max_length: Maximum allowed query length.
        """
        self._min_length = min_length
        self._max_length = max_length

    @property
    def name(self) -> str:
        """The name of the validator."""
        return "InputValidator"

    def validate(self, query: str, metadata: dict[str, Any] | None = None) -> tuple[bool, str | None]:
        """Validate query length, non-emptiness, unicode control chars, and metadata.

        Args:
            query: User prompt query string.
            metadata: Correlation and metadata dictionary.

        Returns:
            A tuple of (is_valid, error_message).
        """
        is_valid = True
        err_msg: str | None = None

        # 1. Empty or whitespace check
        if not query or not query.strip():
            is_valid = False
            err_msg = "Query cannot be empty or contain only whitespace."

        # 2. Length constraints check
        if is_valid:
            val_len = len(query)
            if val_len < self._min_length:
                is_valid = False
                err_msg = f"Query length {val_len} is less than minimum length {self._min_length}."
            elif val_len > self._max_length:
                is_valid = False
                err_msg = f"Query length {val_len} exceeds maximum length {self._max_length}."

        # 3. Unicode control characters check (except spacing like tab and newline)
        if is_valid:
            for char in query:
                category = unicodedata.category(char)
                if category.startswith("C") and char not in "\n\r\t":
                    is_valid = False
                    err_msg = f"Query contains unsupported unicode control character: {char!r}."
                    break

        # 4. Invalid metadata check
        if is_valid and metadata is not None:
            if not isinstance(metadata, dict):
                is_valid = False
                err_msg = "Metadata must be a dictionary."
            elif "request_id" in metadata and not isinstance(metadata["request_id"], str):
                is_valid = False
                err_msg = "Invalid metadata: request_id must be a string."

        return is_valid, err_msg


class CategoryValidator:
    """Validator checking if the query aligns with supported product categories."""

    def __init__(self, laptop_keywords: list[str] | None = None, mobile_keywords: list[str] | None = None) -> None:
        """Initialize the CategoryValidator with configurable keywords.

        Args:
            laptop_keywords: Keywords indicating laptop-related queries.
            mobile_keywords: Keywords indicating mobile-related queries.
        """
        self._laptop_keywords = laptop_keywords if laptop_keywords is not None else LAPTOP_KEYWORDS
        self._mobile_keywords = mobile_keywords if mobile_keywords is not None else MOBILE_KEYWORDS

    @property
    def name(self) -> str:
        """The name of the validator."""
        return "CategoryValidator"

    def validate(self, query: str, metadata: dict[str, Any] | None = None) -> tuple[bool, str | None]:
        """Validate that the query pertains to Laptops or Mobile Phones.

        Args:
            query: User prompt query string.
            metadata: Context metadata dictionary.

        Returns:
            A tuple of (is_valid, error_message).
        """
        lowered_query = query.lower()

        # Check laptop keywords with word boundaries and optional plural 's'
        for kw in self._laptop_keywords:
            pattern = rf"\b{re.escape(kw.lower())}s?\b"
            if re.search(pattern, lowered_query):
                return True, None

        # Check mobile keywords with word boundaries and optional plural 's'
        for kw in self._mobile_keywords:
            pattern = rf"\b{re.escape(kw.lower())}s?\b"
            if re.search(pattern, lowered_query):
                return True, None

        return False, "Query is outside the supported product categories (Laptop, Mobile Phone)."
