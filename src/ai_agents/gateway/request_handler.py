"""AI Request Handler responsible for parsing, validating, and normalizing client requests."""


from src.ai_agents.metadata import RequestMetadata
from src.ai_agents.schemas.request import AIRequest
from src.ai_agents.utils.ids import (
    generate_conversation_id,
    generate_request_id,
)


class AIRequestHandler:
    """Handles parsing, validation, and ID normalization for incoming AI requests."""

    def handle(
        self,
        prompt: str,
        conversation_id: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        metadata: RequestMetadata | None = None,
    ) -> AIRequest:
        """Parse raw query arguments and returns a validated Pydantic AIRequest model.

        Fills in missing correlation, session, and tracing identifiers automatically.

        Args:
            prompt: Raw user-input prompt text.
            conversation_id: Unique chat conversation identifier.
            request_id: Unique client transaction request identifier.
            trace_id: OpenTelemetry trace correlation identifier.
            metadata: Incoming client network or environment metadata.

        Returns:
            A validated and structured AIRequest model.
        """
        resolved_req_id = request_id or generate_request_id()
        resolved_conv_id = conversation_id or generate_conversation_id()

        if not metadata:
            metadata = RequestMetadata(
                request_id=resolved_req_id,
                client_ip=None,
                user_agent=None,
            )

        # AIRequest constructor will execute Pydantic validators on prompt
        return AIRequest(
            prompt=prompt,
            conversation_id=resolved_conv_id,
            request_id=resolved_req_id,
            metadata=metadata,
        )
