"""Notification Repository implementation for Phase 7.

This module houses the NotificationRepository class providing custom queries for user alerts,
unread notifications, badging statistics, and status marks.
"""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import RepositoryError
from src.models.notification import Notification
from src.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Repository handling custom data operations for the Notification entity."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize NotificationRepository.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        super().__init__(session, Notification)

    async def get_unread_count(self, user_id: UUID) -> int:
        """Fetch total count of unread notifications for a user.

        Optimized using our composite index idx_notifications_user_unread.

        Args:
            user_id: Unique UUID of the user.

        Returns:
            Integer representing unread alert counts.
        """
        return await self.count(user_id=user_id, is_read=False)

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Bulk update all unread user notifications to read.

        Runs a single efficient bulk update query on the database.

        Args:
            user_id: Unique UUID of the user.

        Returns:
            Integer representing the number of updated records.

        Raises:
            RepositoryError: If the bulk update fails.
        """
        try:
            stmt = (
                update(Notification)
                .where(Notification.user_id == user_id, Notification.is_read.is_(False))
                .values(is_read=True)
            )
            result = await self.session.execute(stmt)
            await self.session.flush()
            rowcount = getattr(result, "rowcount", 0)
            return rowcount if rowcount is not None else 0
        except Exception as exc:
            await self.session.rollback()
            raise RepositoryError(
                f"Failed to bulk update notifications to read for user {user_id}",
                details={"error": str(exc)},
            ) from exc

    async def get_user_notifications(
        self,
        user_id: UUID,
        *,
        only_unread: bool = False,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Sequence[Notification]:
        """Fetch notifications sent to a user, sorted newest first.

        Args:
            user_id: Unique UUID of the user.
            only_unread: If True, filters out read alerts.
            page: 1-based page.
            page_size: limit per page.

        Returns:
            A sequence of Notification instances.
        """
        filters: dict[str, Any] = {"user_id": user_id}
        if only_unread:
            filters["is_read"] = False

        return await self.get_all(
            filters=filters,
            sort_by=["-sent_at"],
            page=page,
            page_size=page_size,
        )
