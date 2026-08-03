"""Abstract base contract for LLM API providers."""

from collections.abc import AsyncGenerator
from typing import Protocol, runtime_checkable

from src.ai_agents.schemas.request import AIRequest
from src.ai_agents.schemas.response import AIResponse


@runtime_checkable
class BaseLLMClient(Protocol):
    """Protocol defining the core execution boundary for LLM API clients."""

    async def generate(self, request: AIRequest) -> AIResponse:
        """Submit a completed request to the model provider for non-streaming response.

        Args:
            request: Formatted AIRequest containing prompt, settings, and context.

        Returns:
            AIResponse detailing the raw generated content and token metrics.
        """
        ...

    def generate_stream(self, request: AIRequest) -> AsyncGenerator[AIResponse, None]:
        """Submit a request to the model provider and yield response chunks in real-time.

        Args:
            request: Formatted AIRequest.

        Yields:
            Response chunks containing partial text updates and metadata.
        """
        ...
