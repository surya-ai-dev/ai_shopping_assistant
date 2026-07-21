"""Domain model for Data Quality Assessment Reports."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class DataQualityReport(BaseModel):
    """Product data quality evaluation report model."""

    product_id: str | None = Field(default=None, description="Evaluated Product UUID")
    site_id: str = Field(..., description="Target site identifier")
    completeness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of populated required/optional fields"
    )
    missing_fields: list[str] = Field(
        default_factory=list, description="List of unpopulated expected attributes"
    )
    invalid_fields: list[str] = Field(
        default_factory=list, description="List of attributes failing validation checks"
    )
    parse_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence rating of parser extraction"
    )
    overall_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Weighted aggregate quality score"
    )
    is_passed: bool = Field(..., description="Flag indicating if item passes threshold")

    assessment_details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
