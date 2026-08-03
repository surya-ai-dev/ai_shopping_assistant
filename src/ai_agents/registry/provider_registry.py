"""Registry for managing and resolving LLM provider implementations."""


from src.ai_agents.contracts.llm import BaseLLMClient
from src.ai_agents.enums.provider import ProviderEnum
from src.ai_agents.exceptions import GatewayException


class ProviderRegistry:
    """Registry class to map ProviderEnum options to concrete LLM provider clients."""

    def __init__(self) -> None:
        self._registry: dict[ProviderEnum, type[BaseLLMClient]] = {}

    def register(self, provider: ProviderEnum, client_cls: type[BaseLLMClient]) -> None:
        """Register a concrete LLM provider class with the system.

        Args:
            provider: The target provider enum code.
            client_cls: Concrete implementation class satisfying BaseLLMClient.
        """
        self._registry[provider] = client_cls

    def get(self, provider: ProviderEnum) -> type[BaseLLMClient]:
        """Retrieve the registered class for the target provider enum.

        Args:
            provider: The provider key to look up.

        Returns:
            The registered class.

        Raises:
            GatewayException: If the provider has not been registered.
        """
        if provider not in self._registry:
            raise GatewayException(
                message=f"LLM Provider '{provider}' is not registered in the system.",
                error_code="AI_PROVIDER_UNREGISTERED",
            )
        return self._registry[provider]
