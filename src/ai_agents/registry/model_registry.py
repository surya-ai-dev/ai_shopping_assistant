"""Registry for managing and resolving LLM model size configurations."""

from src.ai_agents.enums.model import ModelSizeEnum
from src.ai_agents.enums.provider import ProviderEnum
from src.ai_agents.exceptions import GatewayException


class ModelRegistry:
    """Registry class to manage model definitions and map names to ModelSizeEnum classes."""

    def __init__(self) -> None:
        self._registry: dict[tuple[ProviderEnum, str], ModelSizeEnum] = {}

    def register(self, provider: ProviderEnum, model_name: str, size: ModelSizeEnum) -> None:
        """Register a specific model and its classification size with the system.

        Args:
            provider: Target provider enum.
            model_name: Name/identifier of the model.
            size: Classification size (e.g., small, medium, large).
        """
        self._registry[(provider, model_name.lower())] = size

    def get_size(self, provider: ProviderEnum, model_name: str) -> ModelSizeEnum:
        """Look up the size category for a given model.

        Args:
            provider: Associated provider enum.
            model_name: Name of the model.

        Returns:
            The registered ModelSizeEnum.

        Raises:
            GatewayException: If the model is not found in the registry.
        """
        key = (provider, model_name.lower())
        if key not in self._registry:
            raise GatewayException(
                message=f"Model '{model_name}' for provider '{provider}' is not registered.",
                error_code="AI_MODEL_UNREGISTERED",
            )
        return self._registry[key]
