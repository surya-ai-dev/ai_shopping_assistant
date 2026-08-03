"""Pydantic v2 schemas representing the active Execution Context of the AI pipeline."""

from typing import Any

from pydantic import BaseModel, Field

from src.ai_agents.metadata import SessionMetadata, TracingMetadata


class ContextMessage(BaseModel):
    """A single turn of dialog history in the execution context."""

    role: str = Field(..., description="Author role (e.g. user, assistant, system).")
    content: str = Field(..., description="Message text content.")
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp string.")


class ExecutionContext(BaseModel):
    """Complete runtime context shared across gateway, router, and planners."""

    session_id: str = Field(..., description="Unique UUID for the active user session.")
    conversation_id: str = Field(..., description="Unique UUID tracking the active conversation thread.")
    history: list[ContextMessage] = Field(
        default_factory=list,
        description="Thread logs loaded from cache/memory."
    )
    user_preferences: dict[str, Any] = Field(
        default_factory=dict,
        description="Loaded preferences, OS choices, or brand parameters."
    )
    products_in_context: list[str] = Field(
        default_factory=list,
        description="Unique database IDs of products loaded in context during this query."
    )
    variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Dynamic variables computed during plan execution."
    )
    session_metadata: SessionMetadata | None = Field(
        default=None,
        description="Optional session lifecycle parameters."
    )
    tracing_metadata: TracingMetadata | None = Field(
        default=None,
        description="Correlation identifiers for distributed tracing."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "8a52e9f1-3329-4b68-98e3-92f582046842",
                "conversation_id": "8a52e9f1-3329-4b68-98e3-92f582046842",
                "history": [
                    {
                        "role": "user",
                        "content": "I am looking for a mobile phone.",
                        "timestamp": "2026-08-03T15:35:00Z"
                    }
                ],
                "user_preferences": {"preferred_brand": "Apple"},
                "products_in_context": ["db://products/iphone-15-pro"],
                "variables": {"comparison_ready": True},
            }
        }
    }
