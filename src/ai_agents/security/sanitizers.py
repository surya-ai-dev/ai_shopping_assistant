"""Request sanitization utilities for cleaning user inputs."""

import re
import unicodedata
from typing import Protocol


class RequestSanitizer(Protocol):
    """Protocol defining the interface for request sanitizers."""

    def sanitize(self, query: str) -> str:
        """Sanitize and clean the input query string.

        Args:
            query: The raw prompt string.

        Returns:
            The sanitized prompt string.
        """
        ...


class DefaultRequestSanitizer:
    """Default sanitizer implementation for cleaning user requests."""

    def sanitize(self, query: str) -> str:
        """Sanitize query by normalizing unicode, trimming, collapsing spaces, and removing control chars.

        Args:
            query: The raw prompt query.

        Returns:
            Sanitized prompt query.
        """
        if not query:
            return ""

        # 1. Normalize Unicode (NFC)
        normalized = unicodedata.normalize("NFC", query)

        # 2. Remove control characters (except common spacing like tab and newline)
        cleaned_chars = []
        for char in normalized:
            category = unicodedata.category(char)
            # Cc: Control, Cf: Format, Cs: Surrogate, Co: Private Use, Cn: Unassigned
            if category.startswith("C") and char not in "\n\r\t":
                continue
            cleaned_chars.append(char)
        cleaned = "".join(cleaned_chars)

        # 3. Collapse duplicate spaces
        # We collapse contiguous spaces to a single space
        collapsed = re.sub(r" +", " ", cleaned)

        # 4. Trim leading and trailing whitespace
        return collapsed.strip()
