"""Pydantic v2 schemas representing incoming API requests for the AI platform."""


from pydantic import BaseModel, Field, field_validator

from src.ai_agents.metadata import RequestMetadata


class AIRequest(BaseModel):
    """Encapsulates the incoming client request payload for the AI assistant."""

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The primary user input text query.",
    )
    conversation_id: str = Field(
        ...,
        description="Unique ID tracking the chat thread.",
    )
    request_id: str = Field(
        ...,
        description="Unique HTTP request correlation ID.",
    )
    metadata: RequestMetadata | None = Field(
        default=None,
        description="Optional telemetry and environment metadata.",
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt_not_empty(cls, v: str) -> str:
        """Ensure the prompt is not just whitespace.

        Args:
            v: Raw prompt string.

        Returns:
            Validated stripped prompt.

        Raises:
            ValueError: If prompt is empty or contains only whitespace.
        """
        if not v.strip():
            raise ValueError("Prompt must contain non-whitespace characters.")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "prompt": "Compare the specifications of iPhone 15 Pro and Galaxy S24.",
                "conversation_id": "8a52e9f1-3329-4b68-98e3-92f582046842",
                "request_id": "008c4501-dfa8-4f20-896c-362890e02d60",
                "metadata": {
                    "request_id": "008c4501-dfa8-4f20-896c-362890e02d60",
                    "timestamp": "2026-08-03T15:35:00Z",
                    "client_ip": "127.0.0.1",
                    "user_agent": "Mozilla/5.0",
                },
            }
        }
    }
