"""SQLAlchemy ORM model for SearchHistory entity.

This module houses the SearchHistory table logging user search inputs,
filters, and results counts for AI recommendations.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.user import User


class SearchHistory(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """SearchHistory entity representing a single logged search transaction."""

    __tablename__ = "search_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    filters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    results_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    searched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="search_histories",
    )

    __table_args__ = (
        Index("idx_search_history_user_date", "user_id", "searched_at"),
        CheckConstraint("results_count >= 0", name="chk_search_history_results_count_positive"),
    )
