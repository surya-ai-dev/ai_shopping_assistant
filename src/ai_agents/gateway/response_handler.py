"""AI Response Handler responsible for formatting outputs and serializing exceptions."""

from typing import Any

from pydantic import BaseModel, Field

from src.ai_agents.exceptions import AIException
from src.ai_agents.schemas.response import AIResponse


class GatewayResponse(BaseModel):
    """Standardized response envelope returned by the AI Gateway to client callers."""

    success: bool = Field(..., description="Flag indicating if the query succeeded.")
    response: AIResponse | None = Field(default=None, description="Enclosed successful response details.")
    error_code: str | None = Field(default=None, description="Standardized error code classification.")
    error_message: str | None = Field(default=None, description="Human-readable description of the error.")
    error_details: dict[str, Any] | None = Field(default=None, description="Additional context info on failures.")
    latency_ms: float = Field(default=0.0, description="Total execution duration in milliseconds.")


class AIResponseHandler:
    """Formatter to standardize outcomes and map internal exceptions into GatewayResponses."""

    def format_success(self, response: AIResponse, latency_ms: float) -> GatewayResponse:
        """Envelops a successful AIResponse into a GatewayResponse.

        Args:
            response: Output generated from downstream planners/LLMs.
            latency_ms: Millisecond runtime tracking duration.

        Returns:
            GatewayResponse wrapper.
        """
        # Ensure latency is attached
        if "latency_ms" not in response.metadata:
            response.metadata["latency_ms"] = latency_ms

        return GatewayResponse(
            success=True,
            response=response,
            error_code=None,
            error_message=None,
            error_details=None,
            latency_ms=latency_ms,
        )

    def format_exception(
        self,
        exception: Exception,
        conversation_id: str,
        request_id: str,
        latency_ms: float,
    ) -> GatewayResponse:
        """Converts an unhandled or custom exception into a formatted GatewayResponse.

        Args:
            exception: Raised error object.
            conversation_id: Conversation ID tracking thread.
            request_id: Request ID tracking transaction.
            latency_ms: Millisecond runtime tracking duration.

        Returns:
            Standardized GatewayResponse envelope.
        """
        error_code = "AI_UNEXPECTED_ERROR"
        error_message = str(exception)
        error_details = {}

        if isinstance(exception, AIException):
            error_code = exception.error_code
            error_message = exception.message
            error_details = exception.details

        return GatewayResponse(
            success=False,
            response=None,
            error_code=error_code,
            error_message=error_message,
            error_details=error_details,
            latency_ms=latency_ms,
        )
