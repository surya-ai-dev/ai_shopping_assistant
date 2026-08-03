"""Security threat detectors for identifying injection, jailbreaks, SQLi, and XSS."""

import re
from typing import Protocol


class SecurityDetector(Protocol):
    """Protocol defining the interface for security detectors."""

    @property
    def name(self) -> str:
        """The name of the detector."""
        ...

    def detect(self, query: str) -> tuple[bool, str | None, float]:
        """Detect security threats in the query.

        Args:
            query: The user query string.

        Returns:
            A tuple of (threat_detected, reason, confidence).
        """
        ...


class PromptInjectionDetector:
    """Detector for identifying prompt injection attempts (e.g. instruction overrides)."""

    def __init__(self) -> None:
        self._patterns = [
            r"ignore\s+(?:previous\s+)?instructions",
            r"forget\s+(?:your\s+|previous\s+)?rules",
            r"reveal\s+(?:system\s+)?prompt",
            r"developer\s+mode",
            r"act\s+as\s+another\s+ai",
            r"you\s+are\s+now\s+an?\s+\w+",
            r"bypass\s+safety\s+guidelines",
        ]
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self._patterns]

    @property
    def name(self) -> str:
        """The name of the detector."""
        return "PromptInjectionDetector"

    def detect(self, query: str) -> tuple[bool, str | None, float]:
        """Scan the query for prompt injection markers.

        Args:
            query: User query string.

        Returns:
            A tuple of (detected, reason, confidence).
        """
        for pattern in self._compiled:
            match = pattern.search(query)
            if match:
                return True, f"Prompt injection pattern detected: '{match.group(0)}'", 1.0

        return False, None, 0.0


class JailbreakDetector:
    """Detector for identifying jailbreak attempts (e.g. roleplay or safety bypass)."""

    def __init__(self) -> None:
        self._patterns = [
            r"\bpretend\b",
            r"\broleplay\b",
            r"bypass\s+safety",
            r"ignore\s+policy",
            r"do\s+anything\s+now",
            r"\bdan\b",  # Common jailbreak persona
        ]
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self._patterns]

    @property
    def name(self) -> str:
        """The name of the detector."""
        return "JailbreakDetector"

    def detect(self, query: str) -> tuple[bool, str | None, float]:
        """Scan the query for jailbreak markers.

        Args:
            query: User query string.

        Returns:
            A tuple of (detected, reason, confidence).
        """
        for pattern in self._compiled:
            match = pattern.search(query)
            if match:
                return True, f"Jailbreak pattern detected: '{match.group(0)}'", 1.0

        return False, None, 0.0


class SQLInjectionDetector:
    """Detector for identifying SQL Injection syntax and patterns."""

    def __init__(self) -> None:
        self._patterns = [
            r"\bunion\s+(?:all\s+)?select\b",
            r"\bselect\b.*\bfrom\b",
            r"\bdrop\s+table\b",
            r"\bdrop\s+database\b",
            r"\bdelete\s+from\b",
            r"\binsert\s+into\b",
            r"\bupdate\b.*\bset\b",
            r"\bor\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",
            r"\bunion\s+select\b",
            r"['\"];\s*(?:select|drop|delete|update|insert|union)\b",
            r"--",  # SQL Comment marker
            r"/\*", # SQL Block comment start
        ]
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self._patterns]

    @property
    def name(self) -> str:
        """The name of the detector."""
        return "SQLInjectionDetector"

    def detect(self, query: str) -> tuple[bool, str | None, float]:
        """Scan the query for SQL injection patterns.

        Args:
            query: User query string.

        Returns:
            A tuple of (detected, reason, confidence).
        """
        for pattern in self._compiled:
            match = pattern.search(query)
            if match:
                return True, f"SQL injection pattern detected: '{match.group(0)}'", 1.0

        return False, None, 0.0


class XSSDetector:
    """Detector for identifying Cross-Site Scripting (XSS) code/tags."""

    def __init__(self) -> None:
        self._patterns = [
            r"<\s*script[^>]*>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
            r"<\s*iframe[^>]*>",
            r"<\s*svg[^>]*>",
            r"alert\s*\(",
        ]
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self._patterns]

    @property
    def name(self) -> str:
        """The name of the detector."""
        return "XSSDetector"

    def detect(self, query: str) -> tuple[bool, str | None, float]:
        """Scan the query for XSS scripts or event handlers.

        Args:
            query: User query string.

        Returns:
            A tuple of (detected, reason, confidence).
        """
        for pattern in self._compiled:
            match = pattern.search(query)
            if match:
                return True, f"XSS pattern detected: '{match.group(0)}'", 1.0

        return False, None, 0.0
