"""Data schemas and enums for the security layer using Pydantic v2."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SecurityStatus(StrEnum):
    """Safety status classifications for queries."""

    SAFE = "SAFE"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"


class ThreatType(StrEnum):
    """Specific threat and validation categories."""

    NONE = "NONE"
    INVALID_INPUT = "INVALID_INPUT"
    UNSUPPORTED_CATEGORY = "UNSUPPORTED_CATEGORY"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    JAILBREAK = "JAILBREAK"
    SQL_INJECTION = "SQL_INJECTION"
    XSS = "XSS"
    MALFORMED_REQUEST = "MALFORMED_REQUEST"
    UNKNOWN = "UNKNOWN"


class SecuritySeverity(StrEnum):
    """Severity ratings for safety warnings and violations."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ScanReport(BaseModel):
    """Internal scan report detailing outcomes of security validations and detectors.

    This report aggregates findings from checking validation criteria and running
    specialized threat detectors on user prompts.
    """

    input_valid: bool = Field(default=True, description="True if the query inputs conform to format bounds.")
    input_error: str | None = Field(default=None, description="Details of the input validation failure.")

    category_valid: bool = Field(default=True, description="True if the query relates to supported categories.")
    category_error: str | None = Field(default=None, description="Details of the category validation failure.")

    prompt_injection_detected: bool = Field(default=False, description="True if prompt injection was detected.")
    prompt_injection_reason: str | None = Field(default=None, description="Detection explanation.")
    prompt_injection_confidence: float = Field(default=0.0, description="Prompt injection detection confidence score.")

    jailbreak_detected: bool = Field(default=False, description="True if a jailbreak pattern was detected.")
    jailbreak_reason: str | None = Field(default=None, description="Detection explanation.")
    jailbreak_confidence: float = Field(default=0.0, description="Jailbreak detection confidence score.")

    sql_injection_detected: bool = Field(default=False, description="True if SQL injection was detected.")
    sql_injection_reason: str | None = Field(default=None, description="Detection explanation.")
    sql_injection_confidence: float = Field(default=0.0, description="SQL injection detection confidence score.")

    xss_detected: bool = Field(default=False, description="True if a cross-site scripting pattern was detected.")
    xss_reason: str | None = Field(default=None, description="Detection explanation.")
    xss_confidence: float = Field(default=0.0, description="XSS detection confidence score.")


class SecurityResult(BaseModel):
    """Result payload representing the security assessment of a query."""

    status: SecurityStatus = Field(
        ...,
        description="The safety status of the query (SAFE, WARNING, or BLOCKED).",
    )
    threat_type: ThreatType = Field(
        ...,
        description="The primary category of threat detected, if any.",
    )
    severity: SecuritySeverity = Field(
        ...,
        description="The severity rating of the detected issue.",
    )
    reason: str | None = Field(
        default=None,
        description="A message detailing why the query was warnings-flagged or blocked.",
    )
    detected_threats: list[str] = Field(
        default_factory=list,
        description="A list of names of threats detected.",
    )
    sanitized_query: str = Field(
        ...,
        description="The query string after applying normalization and sanitization.",
    )
    confidence: float = Field(
        ...,
        description="Confidence score for the security assessment decision.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context, timing metrics, and details.",
    )
    execution_time_ms: float = Field(
        ...,
        description="Time in milliseconds to perform the security scans.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC Timestamp when the security check occurred.",
    )
    scan_report: ScanReport | None = Field(
        default=None,
        description="Optional full scan report detailing each validator and detector outcome.",
    )
