"""Hierarchical custom exception definitions for the AI Agents platform."""

from typing import Any


class AIException(Exception):
    """Base exception class for all AI platform errors.

    Attributes:
        message: Human-readable explanation of the error.
        error_code: Application-specific classification error code string.
        details: Metadata or dynamic validation info related to the error.
        cause: Underlying base exception that triggered this error.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "AI_GENERIC_ERROR",
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        base_str = f"[{self.error_code}] {self.message}"
        if self.details:
            base_str += f" | Details: {self.details}"
        if self.cause:
            base_str += f" | Triggered by: {type(self.cause).__name__}: {self.cause}"
        return base_str


class GatewayException(AIException):
    """Exception raised during gateway request handling or auth checks."""

    def __init__(
        self,
        message: str,
        error_code: str = "AI_GATEWAY_ERROR",
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, error_code, details, cause)


class PlannerException(AIException):
    """Exception raised by planners or LangGraph routing steps."""

    def __init__(
        self,
        message: str,
        error_code: str = "AI_PLANNER_ERROR",
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, error_code, details, cause)


class ToolException(AIException):
    """Exception raised during tool registration or runtime execution."""

    def __init__(
        self,
        message: str,
        error_code: str = "AI_TOOL_ERROR",
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, error_code, details, cause)


class LLMException(AIException):
    """Exception raised during LLM client invocation or response parsing."""

    def __init__(
        self,
        message: str,
        error_code: str = "AI_LLM_ERROR",
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, error_code, details, cause)


class SecurityException(AIException):
    """Exception raised on detection of prompt injection, jailbreak attempts, or safety triggers."""

    def __init__(
        self,
        message: str,
        error_code: str = "AI_SECURITY_ERROR",
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, error_code, details, cause)
