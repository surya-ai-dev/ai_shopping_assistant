"""Policy configurations defining constraints for the Guardrails Layer."""

from src.ai_agents.guardrails.constants import (
    DEFAULT_MAX_CONVERSATION_AGE_SECONDS,
    DEFAULT_MAX_HISTORY_LENGTH,
    DEFAULT_MAX_TURNS,
    FORBIDDEN_CAPABILITIES,
    SUPPORTED_CAPABILITIES,
    SUPPORTED_CATEGORIES,
    TONE_RULES,
)


class DomainPolicy:
    """Policy restricting system interactions to supported product domains."""

    def __init__(self, allowed_categories: list[str] | None = None) -> None:
        self.policy_name = "DomainPolicy"
        self.policy_version = "1.0.0"
        self.policy_description = (
            "Enforces that query context strictly pertains to supported "
            "shopping domains (Laptops and Mobile Phones)."
        )
        self.allowed_categories = (
            allowed_categories if allowed_categories is not None else SUPPORTED_CATEGORIES
        )


class CapabilityPolicy:
    """Policy restricting assistant operations to valid assistance actions."""

    def __init__(
        self,
        allowed_capabilities: list[str] | None = None,
        forbidden_capabilities: list[str] | None = None,
    ) -> None:
        self.policy_name = "CapabilityPolicy"
        self.policy_version = "1.0.0"
        self.policy_description = (
            "Permits standard product search, comparison, and purchase guidance, "
            "while rejecting unrelated tasks such as coding, translations, and math."
        )
        self.allowed_capabilities = (
            allowed_capabilities if allowed_capabilities is not None else SUPPORTED_CAPABILITIES
        )
        self.forbidden_capabilities = (
            forbidden_capabilities if forbidden_capabilities is not None else FORBIDDEN_CAPABILITIES
        )


class ConversationPolicy:
    """Policy constraining conversation limits to preserve model context and pricing."""

    def __init__(
        self,
        max_turns: int = DEFAULT_MAX_TURNS,
        max_history_length: int = DEFAULT_MAX_HISTORY_LENGTH,
        max_conversation_age_seconds: int = DEFAULT_MAX_CONVERSATION_AGE_SECONDS,
    ) -> None:
        self.policy_name = "ConversationPolicy"
        self.policy_version = "1.0.0"
        self.policy_description = (
            "Limits the session length, input sizes, and temporal age of "
            "active conversations."
        )
        self.max_turns = max_turns
        self.max_history_length = max_history_length
        self.max_conversation_age_seconds = max_conversation_age_seconds


class ResponsePolicy:
    """Policy validating LLM outputs against company tone and leakage rules."""

    def __init__(self, tone_rules: list[str] | None = None) -> None:
        self.policy_name = "ResponsePolicy"
        self.policy_version = "1.0.0"
        self.policy_description = (
            "Validates generated responses for professional tone, correctness, "
            "leak prevention, and compliance."
        )
        self.tone_rules = tone_rules if tone_rules is not None else TONE_RULES
