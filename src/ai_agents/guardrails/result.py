"""Result schemas and enums for the Guardrails Layer using Pydantic v2."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GuardrailStatus(StrEnum):
    """Safety status outputs for queries and responses."""

    ALLOW = "ALLOW"
    MODIFY = "MODIFY"
    REJECT = "REJECT"


class GuardrailResult(BaseModel):
    """Result payload representing the guardrail assessment of a query or response."""

    status: GuardrailStatus = Field(
        ...,
        description="The guardrail execution decision status (ALLOW, MODIFY, or REJECT).",
    )
    reason: str | None = Field(
        default=None,
        description="A message detailing why the query/response was modified or rejected.",
    )
    modified_query: str | None = Field(
        default=None,
        description="The cleaned or altered prompt text, if modifications occurred.",
    )
    system_prompt: str | None = Field(
        default=None,
        description="The dynamically generated system instructions compiled for the LLM.",
    )
    fallback_response: str | None = Field(
        default=None,
        description="Standardized fallback query response if the request/response is rejected.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Telemetry and validation details.",
    )
    execution_time_ms: float = Field(
        ...,
        description="Latency duration of the guardrails check in milliseconds.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC Timestamp when the guardrails check occurred.",
    )
    violated_policy: str | None = Field(
        default=None,
        description="The name of the policy that was violated, if any.",
    )
    validator_name: str | None = Field(
        default=None,
        description="The name of the validator that triggered a violation, if any.",
    )
