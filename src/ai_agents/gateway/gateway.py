"""AI Gateway coordinating lifecycle processing of incoming AI requests."""

from collections.abc import Callable, Coroutine
from typing import Any

from src.ai_agents.gateway.pipeline import AIGatewayPipeline
from src.ai_agents.gateway.response_handler import GatewayResponse
from src.ai_agents.metadata import RequestMetadata, SessionMetadata
from src.ai_agents.schemas.request import AIRequest
from src.ai_agents.schemas.response import AIResponse


class AIGateway:
    """Acts as the single entry point for every AI request.

Coordinates the complete gateway request lifecycle,
initializes execution metadata, invokes the gateway
pipeline, and returns a standardized GatewayResponse.

It contains no business logic and does not directly
interact with planners, tools, repositories,
databases, Redis, or LLM providers.
    """

    def __init__(self, pipeline: AIGatewayPipeline) -> None:
        """Initialize the AI Gateway.

        Args:
            pipeline: Orchestration pipeline instance.
        """
        self._pipeline = pipeline

    async def process_request(
        self,
        prompt: str,
        conversation_id: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        session_id: str | None = None,
        user_preferences: dict[str, Any] | None = None,
        session_metadata: SessionMetadata | None = None,
        metadata: RequestMetadata | None = None,
        next_call: Callable[[AIRequest, str], Coroutine[Any, Any, AIResponse]] | None = None,
    ) -> GatewayResponse:
        """Handles, registers, and routes an incoming request payload.

        Args:
            prompt: User-input string.
            conversation_id: Thread conversation identifier.
            request_id: Transaction correlation identifier.
            trace_id: OpenTelemetry trace correlation identifier.
            session_id: Client session identifier.
            user_preferences: Preferences options map.
            session_metadata: Context session parameters model.
            metadata: Incoming client metadata.
            next_call: Concrete planner/LLM executor callable representing future stages.

        Returns:
            Standardized GatewayResponse envelope.
        """
        return await self._pipeline.run(
            prompt=prompt,
            conversation_id=conversation_id,
            request_id=request_id,
            trace_id=trace_id,
            session_id=session_id,
            user_preferences=user_preferences,
            session_metadata=session_metadata,
            metadata=metadata,
            next_call=next_call,
        )
