"""Gateway execution pipeline coordinating handler and middleware execution steps."""

from collections.abc import Callable, Coroutine
from typing import Any

from src.ai_agents.gateway.context_builder import AIContextBuilder
from src.ai_agents.gateway.middleware import AIGatewayMiddleware
from src.ai_agents.gateway.request_handler import AIRequestHandler
from src.ai_agents.gateway.response_handler import AIResponseHandler, GatewayResponse
from src.ai_agents.metadata import RequestMetadata, SessionMetadata
from src.ai_agents.schemas.request import AIRequest
from src.ai_agents.schemas.response import AIResponse
from src.ai_agents.utils.ids import generate_trace_id
from src.ai_agents.utils.timer import Timer


class AIGatewayPipeline:
    """Orchestrates the sequence of request validation, middleware run, and output response mapping."""

    def __init__(
        self,
        request_handler: AIRequestHandler,
        context_builder: AIContextBuilder,
        middleware: AIGatewayMiddleware,
        response_handler: AIResponseHandler,
    ) -> None:
        """Initialize the pipeline with dependencies.

        Args:
            request_handler: Custom request parser.
            context_builder: Context assembler.
            middleware: Pre/post execution middleware hooks.
            response_handler: Standardized outputs serializer.
        """
        self.request_handler = request_handler
        self.context_builder = context_builder
        self.middleware = middleware
        self.response_handler = response_handler

    async def run(
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
        """Executes the complete gateway request-response lifecycle.

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
        # Start global execution timing
        success = False
        response: AIResponse | None = None
        exception: Exception | None = None

        resolved_trace_id = trace_id or generate_trace_id()
        resolved_conv_id = conversation_id or "unassigned_conv"
        resolved_req_id = request_id or "unassigned_req"
        context_session_id = resolved_conv_id

        with Timer() as timer:
            try:
                # 1. Parse and validate request
                request = self.request_handler.handle(
                    prompt=prompt,
                    conversation_id=conversation_id,
                    request_id=request_id,
                    trace_id=resolved_trace_id,
                    metadata=metadata,
                )
                # Keep tracked IDs updated
                resolved_conv_id = request.conversation_id
                resolved_req_id = request.request_id

                # 2. Compile execution context
                context = self.context_builder.build(
                    request=request,
                    trace_id=resolved_trace_id,
                    session_id=session_id,
                    user_preferences=user_preferences,
                    session_metadata=session_metadata,
                )
                context_session_id = context.session_id

                # 3. If no next_call is defined (e.g. Phase 8.2), mock a default resolution
                if not next_call:
                    async def mock_next(req: AIRequest, trace: str) -> AIResponse:
                        return AIResponse(
                            content="AI Gateway initialized. Lifecycle completed successfully.",
                            conversation_id=req.conversation_id,
                            request_id=req.request_id,
                        )
                    next_call = mock_next

                # 4. Execute next call wrapped in middleware boundary
                response = await self.middleware.execute(
                    request=request,
                    trace_id=resolved_trace_id,
                    next_call=next_call,
                )

                # Attach context details for tracking
                response.metadata["trace_id"] = resolved_trace_id
                response.metadata["session_id"] = context_session_id
                success = True

            except Exception as exc:
                exception = exc

        # Outside the Timer context block, elapsed_ms is fully populated by __exit__
        if success and response is not None:
            return self.response_handler.format_success(
                response=response,
                latency_ms=timer.elapsed_ms,
            )
        else:
            target_exc = exception or RuntimeError("Unknown execution failure.")
            return self.response_handler.format_exception(
                exception=target_exc,
                conversation_id=resolved_conv_id,
                request_id=resolved_req_id,
                latency_ms=timer.elapsed_ms,
            )
