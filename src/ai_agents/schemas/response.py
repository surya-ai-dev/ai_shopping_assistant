"""Pydantic v2 schemas representing AI Platform responses."""

from typing import Any

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Execution token count metrics details."""

    prompt_tokens: int = Field(
        default=0,
        ge=0,
        description="Count of input tokens used.",
    )
    completion_tokens: int = Field(
        default=0,
        ge=0,
        description="Count of output tokens generated.",
    )
    total_tokens: int = Field(
        default=0,
        ge=0,
        description="Total tokens consumed (prompt + completion).",
    )


class AIResponse(BaseModel):
    """Structured response payload returned by the AI assistant."""

    content: str = Field(
        ...,
        description="The generated natural language response text or markdown.",
    )
    conversation_id: str = Field(
        ...,
        description="Unique ID tracking the chat thread.",
    )
    request_id: str = Field(
        ...,
        description="Unique ID corresponding to the trigger request.",
    )
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Self-evaluation score of response validity (0.0 to 1.0).",
    )
    citations: list[str] = Field(
        default_factory=list,
        description="Sources, database IDs, or reference web URLs utilized in compilation.",
    )
    token_usage: TokenUsage = Field(
        default_factory=TokenUsage,
        description="Usage statistics detailing LLM pricing costs.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional debugging, timing, or model routing details.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "content": (
                    "The iPhone 15 Pro features a 3274 mAh battery, "
                    "while the Galaxy S24 features a 4000 mAh battery."
                ),
                "conversation_id": "8a52e9f1-3329-4b68-98e3-92f582046842",
                "request_id": "008c4501-dfa8-4f20-896c-362890e02d60",
                "confidence_score": 0.95,
                "citations": ["db://products/iphone-15-pro", "db://products/galaxy-s24"],
                "token_usage": {
                    "prompt_tokens": 120,
                    "completion_tokens": 35,
                    "total_tokens": 155,
                },
                "metadata": {
                    "provider": "ollama",
                    "model": "llama3.2:3b",
                    "latency_ms": 420.5,
                },
            }
        }
    }
