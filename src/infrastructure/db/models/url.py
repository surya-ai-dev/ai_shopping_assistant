"""SQLAlchemy 2.0 ORM Mapped Model for Discovered URLs and Queue persistence."""

import uuid
from typing import Any

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base, TimestampMixin


class DiscoveredURLORM(Base, TimestampMixin):
    """Discovered URLs database queue model."""

    __tablename__ = "discovered_urls"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    url: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    site_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(32), default="generic", nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)

    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parent_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    __table_args__ = (Index("idx_url_queue_status_priority", "status", "priority", "created_at"),)
