"""Feature flags config model for the AI Agents platform."""

from pydantic import BaseModel, Field


class AIFeatureFlags(BaseModel):
    """Configuration flags to enable or disable specific parts of the AI pipeline."""

    enable_memory: bool = Field(default=True, description="Enable conversation short-term memory.")
    enable_guardrails: bool = Field(default=True, description="Enable topic validation and category guards.")
    enable_streaming: bool = Field(default=True, description="Enable streaming responses.")
    enable_planner: bool = Field(default=True, description="Enable LangGraph multi-step planning.")
    enable_monitoring: bool = Field(default=True, description="Enable Prometheus metrics collection.")
    enable_tracing: bool = Field(default=True, description="Enable OpenTelemetry tracing hooks.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "enable_memory": True,
                "enable_guardrails": True,
                "enable_streaming": True,
                "enable_planner": True,
                "enable_monitoring": True,
                "enable_tracing": True,
            }
        }
    }
