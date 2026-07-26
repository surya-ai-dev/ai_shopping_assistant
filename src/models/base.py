"""Declarative Base configuration for Phase 6 Database Models.

This module provides the central BaseModel class that all application ORM entities
inherit. It integrates with the shared base class defined in the database infrastructure
layer to maintain a unified SQLAlchemy MetaData registry.
"""

from src.infrastructure.db.base import Base


class BaseModel(Base):
    """Abstract base class for all application database models.

    Inherits from the centralized declarative Base to share the same
    SQLAlchemy MetaData registry. This allows foreign key resolution
    and automatic Alembic migration tracking across all modules.
    """

    __abstract__ = True
