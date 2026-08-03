"""Pydantic v2 schemas representing intent classification outputs."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.ai_agents.enums.intent import IntentEnum


class IntentResult(BaseModel):
    """Encapsulates the structured output from intent classification."""

    primary_intent: IntentEnum = Field(..., description="The classified user goal identifier.")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classifier confidence score from 0.0 to 1.0.",
    )
    entities: dict[str, Any] = Field(
        default_factory=dict,
        description="Parsed search entities such as categories, brands, price boundaries, or specs.",
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        """Validate confidence score range.

        Args:
            v: Raw confidence float.

        Returns:
            Validated confidence score.

        Raises:
            ValueError: If confidence is not in the [0.0, 1.0] range.
        """
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0.")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "primary_intent": "COMPARE_PRODUCTS",
                "confidence": 0.98,
                "entities": {
                    "category": "mobile",
                    "products": ["iPhone 15 Pro", "Galaxy S24"],
                },
            }
        }
    }
