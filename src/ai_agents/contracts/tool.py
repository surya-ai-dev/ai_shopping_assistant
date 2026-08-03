"""Abstract base contract for registry-registered agent execution tools."""

from typing import Protocol

from pydantic import BaseModel

from src.ai_agents.schemas.tool import ToolRequest, ToolResponse


class BaseTool(Protocol):
    """Protocol defining attributes and functions for registered agent tools."""

    @property
    def name(self) -> str:
        """Unique identifier name of the tool."""
        ...

    @property
    def description(self) -> str:
        """Detailed description explaining when the LLM should invoke the tool."""
        ...

    @property
    def args_schema(self) -> type[BaseModel]:
        """Pydantic model schema defining the required execution inputs."""
        ...

    async def execute(self, request: ToolRequest) -> ToolResponse:
        """Execute the tool's business logic using repositories.

        Args:
            request: The tool execution request containing arguments.

        Returns:
            The structured ToolResponse enclosing results or errors.
        """
        ...
