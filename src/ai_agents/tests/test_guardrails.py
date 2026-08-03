"""Unit tests for the AI Guardrails Layer (Phase 8.4)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from src.ai_agents.guardrails import (
    CapabilityValidator,
    ConversationPolicy,
    ConversationValidator,
    DefaultFallbackGenerator,
    DefaultPromptBuilder,
    DefaultResponseFilter,
    DomainValidator,
    GuardrailResult,
    GuardrailsEngine,
    GuardrailStatus,
)


def test_domain_validator() -> None:
    """Verify that DomainValidator matches laptops and mobiles and blocks off-topic categories."""
    validator = DomainValidator()

    # Allowed Laptop/Mobile queries
    assert validator.validate("Compare Macbook specs")[0] is True
    assert validator.validate("iphone 15 price in USD")[0] is True

    # Blocked queries
    is_allowed, reason = validator.validate("Show me headphones")
    assert is_allowed is False
    assert "outside the supported" in reason  # type: ignore

    is_allowed, reason = validator.validate("Compare shoes on Amazon")
    assert is_allowed is False


def test_capability_validator() -> None:
    """Verify that CapabilityValidator filters out off-topic requests like coding, math, essays, etc."""
    validator = CapabilityValidator()

    # Supported capabilities
    assert validator.validate("recommend products under $1000")[0] is True
    assert validator.validate("compare specs of dell xps 13 and macbook air")[0] is True

    # Blocked coding
    is_allowed, reason = validator.validate("write a python function to parse json")
    assert is_allowed is False
    assert "coding" in reason  # type: ignore

    # Blocked essay
    is_allowed, reason = validator.validate("write an essay about dragons")
    assert is_allowed is False
    assert "essay writing" in reason  # type: ignore

    # Blocked translation
    is_allowed, reason = validator.validate("translate 'hello' to spanish")
    assert is_allowed is False
    assert "translation" in reason  # type: ignore

    # Blocked math
    is_allowed, reason = validator.validate("what is the sum of 234 and 567")
    assert is_allowed is False
    assert "math" in reason  # type: ignore

    # Blocked general knowledge
    is_allowed, reason = validator.validate("who is the capital of France?")
    assert is_allowed is False
    assert "general knowledge" in reason  # type: ignore


def test_conversation_validator() -> None:
    """Verify that ConversationValidator checks length, turns count, age, and empty states."""
    policy = ConversationPolicy(max_turns=3, max_history_length=50, max_conversation_age_seconds=10)
    validator = ConversationValidator(policy=policy)

    # Valid
    assert validator.validate("Compare dell laptops")[0] is True

    # Empty query
    is_allowed, reason = validator.validate("   ")
    assert is_allowed is False
    assert "Empty query" in reason  # type: ignore

    # Size limit
    is_allowed, reason = validator.validate("a" * 51)
    assert is_allowed is False
    assert "exceeds maximum allowed limit" in reason  # type: ignore

    # Turns limit
    is_allowed, reason = validator.validate("specs", metadata={"turn_count": 4})
    assert is_allowed is False
    assert "turn count" in reason  # type: ignore

    # Age limit (expired)
    old_time = (datetime.now(UTC) - timedelta(seconds=20)).isoformat()
    is_allowed, reason = validator.validate("specs", metadata={"started_at": old_time})
    assert is_allowed is False
    assert "expired" in reason  # type: ignore


def test_prompt_builder() -> None:
    """Verify that PromptBuilder builds dynamic system instructions with versions and segments."""
    builder = DefaultPromptBuilder()
    prompt = builder.build_system_prompt("Compare MacBook Air M4 and Dell XPS 13")

    assert "# Prompt Version: 1.0.0" in prompt
    assert "# Policy Version: 1.0.0" in prompt
    assert "AI Shopping Assistant" in prompt
    assert "Laptop" in prompt
    assert "Mobile Phone" in prompt
    assert "User Prompt:" in prompt


def test_response_filter() -> None:
    """Verify that ResponseFilter catches prompt leaks, hallucinations, and architecture disclosures."""
    filt = DefaultResponseFilter()

    # Allow clean response
    status, reason = filt.filter_response(
        "macbook air", "I recommend the Apple MacBook Air M3, it has 8GB RAM."
    )
    assert status == GuardrailStatus.ALLOW
    assert reason is None

    # Block empty response
    status, reason = filt.filter_response("macbook", "")
    assert status == GuardrailStatus.REJECT
    assert "empty response" in reason.lower()  # type: ignore

    # Block prompt leak
    status, reason = filt.filter_response("macbook", "You are an AI Shopping Assistant. Supported categories:")
    assert status == GuardrailStatus.REJECT
    assert "prompt leakage" in reason.lower()  # type: ignore

    # Block architecture leak
    status, reason = filt.filter_response("macbook", "We run PostgreSQL on the backend.")
    assert status == GuardrailStatus.REJECT
    assert "architecture disclosure" in reason.lower()  # type: ignore

    # Block category hallucination
    status, reason = filt.filter_response("macbook", "I recommend the Sony 65-inch television.")
    assert status == GuardrailStatus.REJECT
    assert "unsupported category" in reason.lower()  # type: ignore


def test_fallback_generator() -> None:
    """Verify fallback response generations."""
    generator = DefaultFallbackGenerator()
    assert generator.unsupported_domain() == "I currently support Laptop and Mobile Phone shopping only."
    assert generator.unsupported_capability() == "I cannot perform coding or general knowledge tasks."
    assert generator.unsafe_response() == "I couldn't generate a response that satisfies the platform policies."


def test_guardrails_engine_pre_llm() -> None:
    """Verify that GuardrailsEngine check_request processes pre-LLM pipeline."""
    engine = GuardrailsEngine()

    # 1. Allowed request
    res_allow: GuardrailResult = engine.check_request(
        "Compare MacBook Air M4 and Dell XPS 13",
        metadata={"request_id": "test_req_456"},
    )
    assert res_allow.status == GuardrailStatus.ALLOW
    assert res_allow.system_prompt is not None
    assert "Apple" not in res_allow.system_prompt  # No hardcoding user query in prompts beyond target reference
    assert res_allow.metadata["correlation_id"] == "test_req_456"
    assert res_allow.execution_time_ms > 0.0

    # 2. Blocked domain request
    res_domain = engine.check_request("Show me headphones")
    assert res_domain.status == GuardrailStatus.REJECT
    assert res_domain.fallback_response == "I currently support Laptop and Mobile Phone shopping only."
    assert res_domain.violated_policy == "DomainPolicy"
    assert res_domain.validator_name == "DomainValidator"

    # 3. Blocked capability request
    res_cap = engine.check_request("write a python function")
    assert res_cap.status == GuardrailStatus.REJECT
    assert res_cap.fallback_response == "I cannot perform coding or general knowledge tasks."
    assert res_cap.violated_policy == "CapabilityPolicy"
    assert res_cap.validator_name == "CapabilityValidator"


def test_guardrails_engine_post_llm() -> None:
    """Verify that GuardrailsEngine check_response processes post-LLM pipeline."""
    engine = GuardrailsEngine()

    # 1. Allowed response
    res_allow = engine.check_response(
        "macbook",
        "I recommend the MacBook Air with 16GB RAM.",
        metadata={"request_id": "test_req_789"},
    )
    assert res_allow.status == GuardrailStatus.ALLOW
    assert res_allow.metadata["correlation_id"] == "test_req_789"

    # 2. Blocked hallucinated response
    res_reject = engine.check_response(
        "macbook",
        "I recommend you check the Samsung OLED TV model.",
    )
    assert res_reject.status == GuardrailStatus.REJECT
    assert res_reject.violated_policy == "ResponsePolicy"
    assert res_reject.validator_name == "ResponseFilter"
    assert res_reject.fallback_response == "I couldn't generate a response that satisfies the platform policies."


def test_guardrails_engine_error_handling() -> None:
    """Verify that GuardrailsEngine pre-LLM and post-LLM handle internal errors gracefully without crashing."""
    # Define a broken validator that raises an exception
    class BrokenValidator:
        @property
        def name(self) -> str:
            return "BrokenValidator"

        def validate(self, query: str, metadata: dict[str, Any] | None = None) -> tuple[bool, str | None]:
            raise RuntimeError("Broken validator database query error!")

    # Define a broken filter
    class BrokenFilter:
        def filter_response(self, query: str, response_text: str) -> tuple[GuardrailStatus, str | None]:
            raise RuntimeError("Broken filter network error!")

    engine = GuardrailsEngine(
        validators=[BrokenValidator()],
        response_filter=BrokenFilter(),
    )

    # Pre-LLM check catches error safely
    res_req = engine.check_request("Compare laptops")
    assert res_req.status == GuardrailStatus.REJECT
    assert "Internal guardrails engine check failure" in res_req.reason  # type: ignore
    assert res_req.fallback_response == "I couldn't generate a response that satisfies the platform policies."
    assert res_req.violated_policy == "SystemFaultPolicy"
    assert res_req.validator_name == "GuardrailsEngine"

    # Post-LLM check catches error safely
    res_res = engine.check_response("Compare laptops", "dell xps 13 is recommended.")
    assert res_res.status == GuardrailStatus.REJECT
    assert "Internal guardrails engine check failure" in res_res.reason  # type: ignore
    assert res_res.fallback_response == "I couldn't generate a response that satisfies the platform policies."
    assert res_res.violated_policy == "SystemFaultPolicy"
    assert res_res.validator_name == "GuardrailsEngine"
