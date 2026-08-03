"""Validators for checking queries against domain, capability, and conversation policies."""

import re
from datetime import UTC, datetime
from typing import Any, Protocol

from src.ai_agents.guardrails.constants import (
    LAPTOP_KEYWORDS,
    MOBILE_KEYWORDS,
)
from src.ai_agents.guardrails.policies import (
    CapabilityPolicy,
    ConversationPolicy,
    DomainPolicy,
)


class GuardrailValidator(Protocol):
    """Protocol defining the interface for all guardrail input validators."""

    @property
    def name(self) -> str:
        """The name of the validator."""
        ...

    def validate(self, query: str, metadata: dict[str, Any] | None = None) -> tuple[bool, str | None]:
        """Validate an incoming user query.

        Args:
            query: The input query string.
            metadata: Telemetry and context parameters.

        Returns:
            A tuple of (is_allowed, reason).
        """
        ...


class DomainValidator:
    """Validator enforcing that queries stay within laptop and mobile phone categories."""

    def __init__(self, policy: DomainPolicy | None = None) -> None:
        """Initialize the DomainValidator.

        Args:
            policy: Custom DomainPolicy settings.
        """
        self._policy = policy or DomainPolicy()

    @property
    def name(self) -> str:
        """The name of the validator."""
        return "DomainValidator"

    def validate(self, query: str, metadata: dict[str, Any] | None = None) -> tuple[bool, str | None]:
        """Validate if the query belongs to Laptops or Mobile Phones.

        Args:
            query: The user query string.
            metadata: Optional correlation context.

        Returns:
            A tuple of (is_allowed, reason).
        """
        lowered_query = query.lower()

        # Combine keywords from domain categories
        keywords = []
        if "laptop" in self._policy.allowed_categories:
            keywords.extend(LAPTOP_KEYWORDS)
        if "mobile phone" in self._policy.allowed_categories:
            keywords.extend(MOBILE_KEYWORDS)

        # Enforce exact word or plural matches to prevent partial matching (e.g. headphones)
        for kw in keywords:
            pattern = rf"\b{re.escape(kw.lower())}s?\b"
            if re.search(pattern, lowered_query):
                return True, None

        return False, "Query is outside the supported product domains (Laptop, Mobile Phone)."


class CapabilityValidator:
    """Validator checking for off-topic requests like coding, math, translation, or essays."""

    def __init__(self, policy: CapabilityPolicy | None = None) -> None:
        """Initialize the CapabilityValidator.

        Args:
            policy: Custom CapabilityPolicy settings.
        """
        self._policy = policy or CapabilityPolicy()

    @property
    def name(self) -> str:
        """The name of the validator."""
        return "CapabilityValidator"

    def validate(self, query: str, metadata: dict[str, Any] | None = None) -> tuple[bool, str | None]:
        """Validate that the query capability is permitted.

        Args:
            query: The user query string.
            metadata: Optional correlation context.

        Returns:
            A tuple of (is_allowed, reason).
        """
        lowered_query = query.lower()

        # Check coding indicators
        if "coding" in self._policy.forbidden_capabilities:
            coding_patterns = [
                r"\bpython\b", r"\bjavascript\b", r"\bjava\b", r"\bc\+\+\b",
                r"\bhtml\b", r"\bcss\b", r"\bcoding\b", r"\bprogramming\b",
                r"\bwrite a function\b", r"\bdef\s+\w+\b", r"\bclass\s+\w+\b",
                r"\bfunction\b", r"\bsyntax\b", r"\bcode\b"
            ]
            for p in coding_patterns:
                if re.search(p, lowered_query):
                    msg = (
                        "The capability 'coding' is not supported. "
                        "I can only assist with laptop and mobile phone shopping."
                    )
                    return False, msg

        # Check essay/writing indicators
        if "essay writing" in self._policy.forbidden_capabilities:
            essay_patterns = [
                r"\bessay\b", r"\bwrite a story\b", r"\bwrite a poem\b",
                r"\bparagraph about\b", r"\bwrite an article\b"
            ]
            for p in essay_patterns:
                if re.search(p, lowered_query):
                    msg = (
                        "The capability 'essay writing' is not supported. "
                        "I can only assist with laptop and mobile phone shopping."
                    )
                    return False, msg

        # Check translation indicators
        if "translation" in self._policy.forbidden_capabilities:
            translation_patterns = [
                r"\btranslate\b", r"\btranslation\b", r"\bhow to say\b",
                r"\bin spanish\b", r"\bin french\b", r"\bin german\b"
            ]
            for p in translation_patterns:
                if re.search(p, lowered_query):
                    msg = (
                        "The capability 'translation' is not supported. "
                        "I can only assist with laptop and mobile phone shopping."
                    )
                    return False, msg

        # Check math indicators
        if "math" in self._policy.forbidden_capabilities:
            math_patterns = [
                r"\bsolve\b", r"\bcalculate\b", r"\bequation\b", r"\bsum of\b",
                r"\bdivided by\b", r"\bmultiplied by\b", r"\bplus\b", r"\bminus\b"
            ]
            for p in math_patterns:
                # To prevent blocking normal price searches like "$500 minus tax" or similar, we check
                # for mathematical questions specifically if they look like calculator requests.
                if re.search(p, lowered_query) and any(char.isdigit() for char in lowered_query):
                    msg = (
                        "The capability 'math' is not supported. "
                        "I can only assist with laptop and mobile phone shopping."
                    )
                    return False, msg

        # Check general knowledge indicators
        if "general knowledge" in self._policy.forbidden_capabilities:
            gk_patterns = [
                r"\bwho is\b", r"\bwhy is the sky\b", r"\bcapital of\b",
                r"\bhistory of\b", r"\bwhat is the speed of light\b"
            ]
            for p in gk_patterns:
                if re.search(p, lowered_query):
                    msg = (
                        "The capability 'general knowledge' is not supported. "
                        "I can only assist with laptop and mobile phone shopping."
                    )
                    return False, msg

        return True, None


class ConversationValidator:
    """Validator enforcing turns limits, query size limits, and conversation age bounds."""

    def __init__(self, policy: ConversationPolicy | None = None) -> None:
        """Initialize the ConversationValidator.

        Args:
            policy: Custom ConversationPolicy settings.
        """
        self._policy = policy or ConversationPolicy()

    @property
    def name(self) -> str:
        """The name of the validator."""
        return "ConversationValidator"

    def validate(self, query: str, metadata: dict[str, Any] | None = None) -> tuple[bool, str | None]:
        """Validate conversation boundaries.

        Args:
            query: The user query string.
            metadata: Optional correlation context.

        Returns:
            A tuple of (is_allowed, reason).
        """
        is_allowed = True
        reason: str | None = None

        # 1. Empty conversation state check
        if not query or not query.strip():
            is_allowed = False
            reason = "Empty query input is not allowed."

        # 2. Maximum input size check
        if is_allowed and len(query) > self._policy.max_history_length:
            is_allowed = False
            reason = (
                f"Query length {len(query)} exceeds maximum allowed limit of "
                f"{self._policy.max_history_length} characters."
            )

        meta_dict = metadata or {}

        # 3. Maximum conversation turns check
        if is_allowed:
            turn_count = meta_dict.get("turn_count", 0)
            if not isinstance(turn_count, int):
                turn_count = 0  # Fallback logic for invalid metadata

            if turn_count > self._policy.max_turns:
                is_allowed = False
                reason = (
                    f"Conversation turn count {turn_count} exceeds "
                    f"maximum allowed turns of {self._policy.max_turns}."
                )

        # 4. Maximum conversation age check
        if is_allowed:
            started_at = meta_dict.get("started_at")
            if started_at:
                if isinstance(started_at, str):
                    try:
                        # Parse ISO format timestamp
                        started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                    except ValueError:
                        started_at = None

                if isinstance(started_at, datetime):
                    if started_at.tzinfo is None:
                        started_at = started_at.replace(tzinfo=UTC)
                    age_seconds = (datetime.now(UTC) - started_at).total_seconds()
                    if age_seconds > self._policy.max_conversation_age_seconds:
                        is_allowed = False
                        reason = "Conversation session has expired due to age limit."

        return is_allowed, reason
