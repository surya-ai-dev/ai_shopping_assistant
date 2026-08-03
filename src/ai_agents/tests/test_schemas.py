"""Unit tests verifying Pydantic v2 schemas and validation models."""

import pytest
from pydantic import ValidationError

from src.ai_agents.enums.intent import IntentEnum
from src.ai_agents.schemas.intent import IntentResult
from src.ai_agents.schemas.request import AIRequest
from src.ai_agents.schemas.tool import ToolRequest, ToolResponse


def test_ai_request_valid() -> None:
    """Verify AIRequest parses valid inputs."""
    req = AIRequest(
        prompt="Compare laptops",
        conversation_id="conv_123",
        request_id="req_123",
    )
    assert req.prompt == "Compare laptops"
    assert req.conversation_id == "conv_123"


def test_ai_request_invalid_prompt_empty() -> None:
    """Verify AIRequest raises validation error on empty or whitespace prompt."""
    with pytest.raises(ValidationError):
        AIRequest(
            prompt="   ",
            conversation_id="conv_123",
            request_id="req_123",
        )


def test_intent_result_valid() -> None:
    """Verify IntentResult parses correct intent structures."""
    intent = IntentResult(
        primary_intent=IntentEnum.COMPARE_PRODUCTS,
        confidence=0.95,
        entities={"category": "laptop"},
    )
    assert intent.primary_intent == IntentEnum.COMPARE_PRODUCTS
    assert intent.confidence == 0.95


def test_intent_result_invalid_confidence() -> None:
    """Verify IntentResult raises error when confidence is outside [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        IntentResult(
            primary_intent=IntentEnum.COMPARE_PRODUCTS,
            confidence=1.5,
        )


def test_tool_schemas() -> None:
    """Verify ToolRequest and ToolResponse schemas serialize correctly."""
    req = ToolRequest(
        tool_name="spec_lookup",
        arguments={"id": "macbook-air"},
        request_id="req_123",
    )
    assert req.tool_name == "spec_lookup"

    res = ToolResponse(
        tool_name="spec_lookup",
        success=True,
        result={"specs": "M3 Chip"},
        execution_time_ms=15.2,
    )
    assert res.success is True
    assert res.execution_time_ms == 15.2
