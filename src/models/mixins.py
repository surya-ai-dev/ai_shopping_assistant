"""Reusable SQLAlchemy ORM mixins for Phase 6 Database Models.

This module provides common mixins for UUID primary keys, audit timestamps,
soft-delete support, and audit tracking to promote DRY design and schema consistency.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column


@declarative_mixin
class UUIDMixin:
    """Mixin to inject a native PostgreSQL UUID primary key.

    Using native UUID type ensures optimal 16-byte storage size in PostgreSQL
    and supports efficient index traversal compared to 36-byte string UUID representation.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


@declarative_mixin
class TimestampMixin:
    """Mixin to inject standard timezone-aware audit timestamps.

    Stores dates as TIMESTAMPTZ (with timezone in PostgreSQL) using UTC timezone
    standard. Auto-updates updated_at on record changes.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


@declarative_mixin
class SoftDeleteMixin:
    """Mixin to inject logical deletion capabilities.

    Instead of hard DELETE statements, records are marked as is_deleted = True,
    preserving historical integrity and relationship linkages.
    """

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    def soft_delete(self) -> None:
        """Mark the entity as logically deleted."""
        self.is_deleted = True


@declarative_mixin
class AuditMixin:
    """Mixin to track the actors who created or modified the record.

    Useful for security compliance and tracking operations.
    References the 'users' table using a foreign key.
    """

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
