"""Pydantic v2 schemas representing agent tool requests and execution outputs."""

from typing import Any

from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    """Encapsulates execution arguments passed to a registered agent tool."""

    tool_name: str = Field(..., description="Target tool identifier matching its registered registry key.")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key-value arguments satisfying the tool schema.",
    )
    request_id: str = Field(..., description="Unique HTTP request correlation identifier tracking this transaction.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tool_name": "get_price_history",
                "arguments": {"product_model_id": "iphone-15-pro", "days": 30},
                "request_id": "008c4501-dfa8-4f20-896c-362890e02d60",
            }
        }
    }


class ToolResponse(BaseModel):
    """Encapsulates outcome details after tool execution."""

    tool_name: str = Field(..., description="Executing tool name.")
    success: bool = Field(..., description="True if the execution completed without unhandled exceptions.")
    result: dict[str, Any] | None = Field(
        default=None,
        description="Enclosed execution result dictionary on success.",
    )
    error_message: str | None = Field(
        default=None,
        description="Error description explanation on failure.",
    )
    execution_time_ms: float | None = Field(
        default=None,
        ge=0.0,
        description="Time elapsed in milliseconds during tool execution.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "tool_name": "get_price_history",
                "success": True,
                "result": {
                    "average_price": 999.0,
                    "historical_high": 1099.0,
                    "historical_low": 899.0,
                },
                "error_message": None,
                "execution_time_ms": 12.5,
            }
        }
    }
