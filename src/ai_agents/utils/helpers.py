"""General utility helper functions for AI agent operations."""

import re


def sanitize_text(text: str) -> str:
    """Escapes HTML entities and strips non-printable control sequences from inputs.

    Args:
        text: Raw user prompt or scraper text.

    Returns:
        Sanitized and safe string representation.
    """
    # Replace common HTML markup tag syntaxes
    clean = re.sub(r"<[^>]*>", "", text)
    # Strip dangerous terminal escape characters
    clean = "".join(ch for ch in clean if ch.isprintable() or ch in "\n\r\t")
    return clean.strip()


def clean_whitespace(text: str) -> str:
    """Reduces multiple contiguous whitespace blocks and tabs to single spaces.

    Args:
        text: Raw source text.

    Returns:
        Compact string with normalized spacing.
    """
    return re.sub(r"\s+", " ", text).strip()


def estimate_token_count(text: str) -> int:
    """Performs a quick heuristic estimation of token counts based on average word length.

    A common standard is ~4 characters per token or 0.75 words per token.

    Args:
        text: Target text to analyze.

    Returns:
        Heuristic token count integer.
    """
    if not text:
        return 0
    words = text.split()
    # Average rule of thumb: 1.3 tokens per word
    return int(len(words) * 1.3)
