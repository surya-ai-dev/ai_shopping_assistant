"""Response filtering utility to screen LLM response strings before delivery."""

import re
from typing import Final, Protocol

from src.ai_agents.guardrails.policies import ResponsePolicy
from src.ai_agents.guardrails.result import GuardrailStatus

MAX_RESPONSE_LENGTH: Final[int] = 10_000


class ResponseFilter(Protocol):
    """Protocol defining the interface for response filters."""

    def filter_response(self, query: str, response_text: str) -> tuple[GuardrailStatus, str | None]:
        """Validate LLM output against response policies.

        Args:
            query: The user query string.
            response_text: Raw LLM response string.

        Returns:
            A tuple of (decision_status, reason).
        """
        ...


class DefaultResponseFilter:
    """Default response filter checking for leaks, architecture mentions, and hallucinations."""

    def __init__(self, policy: ResponsePolicy | None = None) -> None:
        """Initialize the DefaultResponseFilter.

        Args:
            policy: Custom ResponsePolicy settings.
        """
        self._policy = policy or ResponsePolicy()

    @property
    def name(self) -> str:
        """The name of the filter."""
        return "DefaultResponseFilter"

    def filter_response(self, query: str, response_text: str) -> tuple[GuardrailStatus, str | None]:
        """Filter response against leakage, hallucinations, empty state, and tone violations.

        Args:
            query: User query string.
            response_text: Raw LLM response text.

        Returns:
            A tuple of (decision_status, reason).
        """
        # 1. Empty LLM response validation
        if not response_text or not response_text.strip():
            return GuardrailStatus.REJECT, "Received empty response from the LLM."

        lowered_res = response_text.lower()

        # 2. Prompt Leakage Detection
        prompt_leak_terms = [
            "system prompt", "internal instructions", "forbidden capabilities",
            "supported categories", "prompt version", "policy version",
            "you are an ai shopping assistant"
        ]
        for term in prompt_leak_terms:
            if term in lowered_res:
                return (
                    GuardrailStatus.REJECT,
                    f"Prompt leakage detected: response contains system prompt term '{term}'.",
                )

        # 3. Internal Architecture Leakage Detection
        arch_leak_terms = [
            "postgresql", "redis", "gateway", "planner", "tool registry",
            "scraper", "db pool", "ai gateway", "security layer", "guardrails layer"
        ]
        for term in arch_leak_terms:
            if term in lowered_res:
                return (
                    GuardrailStatus.REJECT,
                    (
                        f"Architecture disclosure detected: response contains "
                        f"system architecture term '{term}'."
                    ),
                )

        # 4. Unsupported Product & Hallucination Detection
        # Check if the response contains recommendations for categories outside laptops/mobiles
        # but only if the user query was safe. If the LLM generates tv or shoes recommendations
        # to a laptop query, it's a hallucination or category leak.
        unsupported_products = [
            "television", "tv", "speaker", "headphones", "camera", "fridge",
            "books", "clothes", "shoes", "flight", "hotel", "grocery", "groceries"
        ]
        for prod in unsupported_products:
            # We match as whole words to avoid sub-word triggers
            pattern = rf"\b{re.escape(prod)}s?\b"
            if re.search(pattern, lowered_res):
                return GuardrailStatus.REJECT, f"Unsupported category recommendation detected: '{prod}'."

        # 5. Response Policy Validation (length check)
        # Check for very large response text (e.g. exceeding 10,000 characters)
        if len(response_text) > MAX_RESPONSE_LENGTH:
            return GuardrailStatus.REJECT, "LLM response length exceeds maximum safe limits."

        return GuardrailStatus.ALLOW, None
