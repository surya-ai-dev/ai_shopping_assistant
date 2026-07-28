"""User Repository implementation for Phase 7.

This module houses the UserRepository class which provides customized query methods
for User entity management, authentication, and state toggles.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import interfaces

from src.models.user import User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository handling custom data operations for the User entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize UserRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, User)

    async def get_by_email(
        self,
        email: str,
        options: Sequence[interfaces.UserDefinedOption] | None = None,
    ) -> User | None:
        """Retrieve a user by their unique email address.

        Args:
            email: User's electronic mail address.
            options: Loader options for eager relationship loading.

        Returns:
            The User instance if found, otherwise None.
        """
        return await self.get_by_field("email", email, options=options)

    async def activate(self, user_id: UUID) -> User | None:
        """Activate a user account.

        Args:
            user_id: Unique UUID of the user.

        Returns:
            The activated User instance, or None if user doesn't exist.
        """
        return await self.update(user_id, {"is_active": True})

    async def deactivate(self, user_id: UUID) -> User | None:
        """Deactivate a user account.

        Args:
            user_id: Unique UUID of the user.

        Returns:
            The deactivated User instance, or None if user doesn't exist.
        """
        return await self.update(user_id, {"is_active": False})

    async def get_active_users(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Sequence[User]:
        """Fetch all active user accounts.

        Args:
            page: 1-based page.
            page_size: limit per page.

        Returns:
            A sequence of active User accounts.
        """
        return await self.get_all(filters={"is_active": True}, page=page, page_size=page_size)
