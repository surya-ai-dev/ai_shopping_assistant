"""Unit tests verifying abstract registries and interface structures."""

from collections.abc import AsyncGenerator

import pytest
from pydantic import BaseModel

from src.ai_agents.enums.model import ModelSizeEnum
from src.ai_agents.enums.provider import ProviderEnum
from src.ai_agents.exceptions import GatewayException, ToolException
from src.ai_agents.registry.model_registry import ModelRegistry
from src.ai_agents.registry.provider_registry import ProviderRegistry
from src.ai_agents.registry.tool_registry import ToolRegistry
from src.ai_agents.schemas.request import AIRequest
from src.ai_agents.schemas.response import AIResponse
from src.ai_agents.schemas.tool import ToolRequest, ToolResponse


class DummyLLMClient:
    """Mock implementation of BaseLLMClient for testing."""

    async def generate(self, request: AIRequest) -> AIResponse:
        return AIResponse(
            content="Mocked response",
            conversation_id=request.conversation_id,
            request_id=request.request_id,
        )

    async def generate_stream(self, request: AIRequest) -> AsyncGenerator[AIResponse, None]:
        yield AIResponse(
            content="Chunk",
            conversation_id=request.conversation_id,
            request_id=request.request_id,
        )


class DummyToolArgs(BaseModel):
    param: str


class DummyTool:
    """Mock implementation of BaseTool for testing."""

    @property
    def name(self) -> str:
        return "dummy_tool"

    @property
    def description(self) -> str:
        return "A dummy test tool"

    @property
    def args_schema(self) -> type[BaseModel]:
        return DummyToolArgs

    async def execute(self, request: ToolRequest) -> ToolResponse:
        return ToolResponse(
            tool_name=self.name,
            success=True,
            result={"output": "success"},
        )


def test_provider_registry() -> None:
    """Verify LLM client provider registration and resolution."""
    registry = ProviderRegistry()
    registry.register(ProviderEnum.OLLAMA, DummyLLMClient)

    resolved_cls = registry.get(ProviderEnum.OLLAMA)
    assert resolved_cls is DummyLLMClient

    with pytest.raises(GatewayException):
        registry.get(ProviderEnum.OPENAI)


def test_tool_registry() -> None:
    """Verify tool registration and resolution flow."""
    registry = ToolRegistry()
    tool = DummyTool()
    registry.register(tool)

    resolved_tool = registry.get("dummy_tool")
    assert resolved_tool is tool

    assert len(registry.list_tools()) == 1

    with pytest.raises(ToolException):
        registry.register(tool)  # Duplicate registration

    with pytest.raises(ToolException):
        registry.get("unknown_tool")


def test_model_registry() -> None:
    """Verify model size registration and lookup."""
    registry = ModelRegistry()
    registry.register(ProviderEnum.OLLAMA, "llama3", ModelSizeEnum.SMALL)

    size = registry.get_size(ProviderEnum.OLLAMA, "llama3")
    assert size == ModelSizeEnum.SMALL

    with pytest.raises(GatewayException):
        registry.get_size(ProviderEnum.OLLAMA, "unknown")
