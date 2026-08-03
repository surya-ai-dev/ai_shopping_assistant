"""Metadata structures for tracking requests, conversations, sessions, and executions."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RequestMetadata(BaseModel):
    """Metadata detailing the origin and context of an incoming request."""

    request_id: str = Field(..., description="Unique UUID assigned to this client request.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time the request was received.")
    client_ip: str | None = Field(default=None, description="Client IP address.")
    user_agent: str | None = Field(default=None, description="Client user agent string.")


class ConversationMetadata(BaseModel):
    """Metadata tracking dialogue sequences and conversational state."""

    conversation_id: str = Field(..., description="Unique UUID tracking the chat thread.")
    user_id: str | None = Field(default=None, description="Associated authenticated user ID.")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when thread was started.")
    turn_count: int = Field(default=0, description="Number of turns completed in this conversation thread.")


class SessionMetadata(BaseModel):
    """Session details related to the active connection lifecycle."""

    session_id: str = Field(..., description="Unique UUID tracking the active HTTP/WebSocket session.")
    auth_token_expires_at: datetime | None = Field(default=None, description="Expiration time of the current auth token.")
    locale: str = Field(default="en_US", description="Local language preference of the client.")
    currency: str = Field(default="USD", description="Default currency code for price representations.")


class TracingMetadata(BaseModel):
    """Tracing attributes to follow executions in OpenTelemetry."""

    trace_id: str = Field(..., description="OpenTelemetry Trace identifier.")
    span_id: str | None = Field(default=None, description="Active execution span identifier.")
    parent_span_id: str | None = Field(default=None, description="Parent trace span identifier.")


class ExecutionMetadata(BaseModel):
    """Execution timing and component routing logs."""

    component_name: str = Field(..., description="Active executor module name.")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp execution started.")
    completed_at: datetime | None = Field(default=None, description="Timestamp execution finished.")
    duration_ms: float | None = Field(default=None, description="Execution duration in milliseconds.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional debug metrics or custom records.")
