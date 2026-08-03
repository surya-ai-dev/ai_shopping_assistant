"""Abstract base contract for AI planning engines (e.g. LangGraph)."""

from typing import Protocol, runtime_checkable

from src.ai_agents.schemas.context import ExecutionContext
from src.ai_agents.schemas.request import AIRequest
from src.ai_agents.schemas.response import AIResponse


@runtime_checkable
class BasePlanner(Protocol):
    """Protocol defining the interface for the LangGraph planning engine."""

    async def execute_plan(self, request: AIRequest, context: ExecutionContext) -> AIResponse:
        """Constructs and executes a multi-step query resolution plan.

        Args:
            request: The client AI request payload.
            context: Active conversation and product execution context.

        Returns:
            The final resolved AIResponse after resolving all plan items.
        """
        ...
