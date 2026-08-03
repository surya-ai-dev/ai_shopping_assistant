"""Registry for managing and resolving agent tools."""

from src.ai_agents.contracts.tool import BaseTool
from src.ai_agents.exceptions import ToolException


class ToolRegistry:
    """Registry class holding all tool executions available for planners."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Add a tool instance to the registry database.

        Args:
            tool: A class implementing the BaseTool protocol.

        Raises:
            ToolException: If a tool with the same name is already registered.
        """
        name = tool.name
        if name in self._tools:
            raise ToolException(
                message=f"Tool with name '{name}' is already registered.",
                error_code="AI_TOOL_DUPLICATE_REGISTRATION",
            )
        self._tools[name] = tool

    def get(self, name: str) -> BaseTool:
        """Fetch a registered tool by its name.

        Args:
            name: Name of the tool.

        Returns:
            The registered BaseTool instance.

        Raises:
            ToolException: If the tool is not found.
        """
        if name not in self._tools:
            raise ToolException(
                message=f"Tool '{name}' not found in the Tool Registry.",
                error_code="AI_TOOL_NOT_FOUND",
            )
        return self._tools[name]

    def list_tools(self) -> list[BaseTool]:
        """Return all registered tools as a list.

        Returns:
            A list containing all registered BaseTool instances.
        """
        return list(self._tools.values())
