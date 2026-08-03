"""Fallback responses generation for guardrail violations."""

from typing import Protocol


class FallbackGenerator(Protocol):
    """Protocol defining the interface for Fallback Generators."""

    def unsupported_domain(self) -> str:
        """Fallback message when the query relates to unsupported product domains.

        Returns:
            The fallback message string.
        """
        ...

    def unsupported_capability(self) -> str:
        """Fallback message when the query requests forbidden capabilities.

        Returns:
            The fallback message string.
        """
        ...

    def unsafe_response(self) -> str:
        """Fallback message when the LLM response violates safety/quality policies.

        Returns:
            The fallback message string.
        """
        ...

    def general_failure(self, reason: str) -> str:
        """General fallback message for any other guardrail rejection.

        Args:
            reason: The reason string for the violation.

        Returns:
            The fallback message string.
        """
        ...


class DefaultFallbackGenerator:
    """Default fallback response generator."""

    def unsupported_domain(self) -> str:
        """Return fallback for unsupported category/domain.

        Returns:
            Fallback response string.
        """
        return "I currently support Laptop and Mobile Phone shopping only."

    def unsupported_capability(self) -> str:
        """Return fallback for unsupported coding, writing, or math.

        Returns:
            Fallback response string.
        """
        return "I cannot perform coding or general knowledge tasks."

    def unsafe_response(self) -> str:
        """Return fallback for filter leakage, hallucination, or safety blocks.

        Returns:
            Fallback response string.
        """
        return "I couldn't generate a response that satisfies the platform policies."

    def general_failure(self, reason: str) -> str:
        """Return standard fallback response.

        Args:
            reason: Error detail string.

        Returns:
            Fallback response string.
        """
        return "I couldn't generate a response that satisfies the platform policies."
