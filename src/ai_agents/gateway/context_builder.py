"""Context Builder responsible for compiling request schemas into the ExecutionContext."""

from typing import Any

from src.ai_agents.metadata import SessionMetadata, TracingMetadata
from src.ai_agents.schemas.context import ExecutionContext
from src.ai_agents.schemas.request import AIRequest


class AIContextBuilder:
    """Builds and populates the execution context frame for query lifecycle stages."""

    def build(
        self,
        request: AIRequest,
        trace_id: str,
        session_id: str | None = None,
        user_preferences: dict[str, Any] | None = None,
        session_metadata: SessionMetadata | None = None,
    ) -> ExecutionContext:
        """Assembles request schemas and tracing attributes into an ExecutionContext.

        Args:
            request: The validated AIRequest model.
            trace_id: OpenTelemetry trace ID.
            session_id: Active session UUID identifier.
            user_preferences: User affinity configurations dictionary.
            session_metadata: Associated session parameters model.

        Returns:
            A populated ExecutionContext.
        """
        # Session ID defaults to conversation_id if not explicitly provided
        resolved_session_id = session_id or request.conversation_id

        # Compile tracing metadata
        tracing_metadata = TracingMetadata(
            trace_id=trace_id,
            span_id=None,
            parent_span_id=None,
        )

        return ExecutionContext(
            session_id=resolved_session_id,
            conversation_id=request.conversation_id,
            history=[],  # No database/cache access in this phase
            user_preferences=user_preferences or {},
            products_in_context=[],
            variables={},
            session_metadata=session_metadata,
            tracing_metadata=tracing_metadata,
        )
