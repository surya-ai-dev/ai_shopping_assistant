"""Abstract base contract for managing conversation and user session memory."""

from collections.abc import Sequence
from typing import Any, Protocol


class BaseMemory(Protocol):
    """Protocol defining persistence boundaries for short-term and preference memory."""

    async def get_conversation_history(self, conversation_id: str, limit: int = 20) -> Sequence[dict[str, Any]]:
        """Retrieve conversation logs/history for the thread.

        Args:
            conversation_id: Unique tracking ID for the chat.
            limit: Maximum dialogue steps/turns to pull.

        Returns:
            A sequence of message mappings containing role and text content.
        """
        ...

    async def save_message(self, conversation_id: str, role: str, content: str) -> None:
        """Persist a message turn to the chat history cache.

        Args:
            conversation_id: Unique tracking ID for the chat.
            role: The author role (e.g. user, assistant, system).
            content: The text content.
        """
        ...

    async def get_user_preferences(self, user_id: str) -> dict[str, Any]:
        """Fetch saved user choices, brand affinities, or budget constraints.

        Args:
            user_id: Target user unique ID string.

        Returns:
            Dictionary containing persistent preference flags.
        """
        ...

    async def save_user_preferences(self, user_id: str, preferences: dict[str, Any]) -> None:
        """Write user preference updates back to persistent storage.

        Args:
            user_id: Target user unique ID string.
            preferences: Updated parameters to write.
        """
        ...

    async def clear_session(self, conversation_id: str) -> None:
        """Clear the cached history for a conversation thread.

        Args:
            conversation_id: Thread ID to delete.
        """
        ...
