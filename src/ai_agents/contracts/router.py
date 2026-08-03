"""Abstract base contract for model routing systems."""

from typing import Protocol

from src.ai_agents.enums.provider import ProviderEnum
from src.ai_agents.schemas.intent import IntentResult


class BaseModelRouter(Protocol):
    """Protocol defining the decision-maker class that assigns LLMs based on intent."""

    def route_model(self, intent: IntentResult) -> tuple[ProviderEnum, str]:
        """Selects the best provider and model version based on intent complexity.

        Args:
            intent: The classified intent and entity detail structures.

        Returns:
            A tuple of (ProviderEnum, ModelNameString) detailing target destination.
        """
        ...
