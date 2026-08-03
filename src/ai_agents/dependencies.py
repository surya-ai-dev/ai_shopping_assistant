"""FastAPI dependency provider functions for injecting AI Platform components."""

from fastapi import Request

from src.ai_agents.contracts.llm import BaseLLMClient
from src.ai_agents.contracts.memory import BaseMemory
from src.ai_agents.contracts.planner import BasePlanner
from src.ai_agents.contracts.router import BaseModelRouter


async def get_llm_client(request: Request) -> BaseLLMClient:
    """Dependency provider for retrieving the configured LLM client interface."""
    # Resolves client from application state loaded at startup.
    client = getattr(request.app.state, "ai_llm_client", None)
    if not client or not isinstance(client, BaseLLMClient):
        raise TypeError("Application state 'ai_llm_client' does not implement BaseLLMClient.")
    return client


async def get_planner(request: Request) -> BasePlanner:
    """Dependency provider for retrieving the active graph execution planner."""
    planner = getattr(request.app.state, "ai_planner", None)
    if not planner or not isinstance(planner, BasePlanner):
        raise TypeError("Application state 'ai_planner' does not implement BasePlanner.")
    return planner


async def get_model_router(request: Request) -> BaseModelRouter:
    """Dependency provider for retrieving the query router."""
    router = getattr(request.app.state, "ai_model_router", None)
    if not router or not isinstance(router, BaseModelRouter):
        raise TypeError("Application state 'ai_model_router' does not implement BaseModelRouter.")
    return router


async def get_memory_manager(request: Request) -> BaseMemory:
    """Dependency provider for retrieving the Redis/Postgres memory interface."""
    memory = getattr(request.app.state, "ai_memory", None)
    if not memory or not isinstance(memory, BaseMemory):
        raise TypeError("Application state 'ai_memory' does not implement BaseMemory.")
    return memory
