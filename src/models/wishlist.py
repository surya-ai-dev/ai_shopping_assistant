"""SQLAlchemy ORM model for Wishlist entity.

This module houses the Wishlist table representing user-curated product folders
and sharing visibility scopes.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel
from src.models.enums import WishlistVisibility
from src.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.user import User
    from src.models.wishlist_item import WishlistItem


class Wishlist(BaseModel, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Wishlist entity representing a user's collection of saved items."""

    __tablename__ = "wishlists"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    visibility: Mapped[WishlistVisibility] = mapped_column(
        Enum(WishlistVisibility, native_enum=False),
        default=WishlistVisibility.PRIVATE,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="wishlists",
    )
    items: Mapped[list["WishlistItem"]] = relationship(
        "WishlistItem",
        back_populates="wishlist",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
