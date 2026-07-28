"""Generic Base Repository implementation for Phase 7.

This module provides BaseRepository, a generic, type-safe async class enclosing
standard CRUD operations, pagination, filtering, sorting, and error logging.
"""

import time
from collections.abc import Sequence
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption

from src.core.exceptions import RepositoryError
from src.core.logging import get_logger
from src.models.base import BaseModel

logger = get_logger(__name__)

# Type variable constrained to BaseModel models
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Generic asynchronous repository for SQLAlchemy ORM models.

    Provides standard CRUD operations, dynamic filtering, sorting,
    eager loading options, transactional boundaries, and unified error mapping.
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        """Initialize repository with session and target model class.

        Args:
            session: Active SQLAlchemy AsyncSession.
            model: Concrete ORM model class.
        """
        self.session = session
        self.model = model

    async def create(self, entity: ModelType) -> ModelType:
        """Add an entity to the session and flush changes.

        Args:
            entity: Instance of the target ORM model.

        Returns:
            The created and flushed ORM model.

        Raises:
            RepositoryError: If an integrity constraint or database error occurs.
        """
        start_time = time.perf_counter()
        logger.debug(f"Creating {self.model.__name__} entity")
        try:
            self.session.add(entity)
            await self.session.flush()
            logger.debug(
                f"Successfully created {self.model.__name__} in {time.perf_counter() - start_time:.4f}s"
            )
            return entity
        except IntegrityError as exc:
            await self.session.rollback()
            logger.error(f"Integrity error creating {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Integrity violation creating {self.model.__name__}",
                details={"error": str(exc)},
            ) from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            logger.error(f"Database error creating {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Database error creating {self.model.__name__}",
                details={"error": str(exc)},
            ) from exc

    async def create_many(self, entities: Sequence[ModelType]) -> Sequence[ModelType]:
        """Add multiple entities to the session and flush.

        Args:
            entities: Sequence of target ORM models.

        Returns:
            The created and flushed ORM models.

        Raises:
            RepositoryError: If a database error occurs.
        """
        start_time = time.perf_counter()
        logger.debug(f"Bulk creating {len(entities)} {self.model.__name__} entities")
        try:
            self.session.add_all(entities)
            await self.session.flush()
            logger.debug(
                f"Successfully created {len(entities)} entities in {time.perf_counter() - start_time:.4f}s"
            )
            return entities
        except SQLAlchemyError as exc:
            await self.session.rollback()
            logger.error(f"Database error bulk creating {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Failed to bulk create {self.model.__name__} entities",
                details={"error": str(exc)},
            ) from exc

    async def get_by_id(
        self,
        entity_id: Any,
        options: Sequence[ORMOption] | None = None,
    ) -> ModelType | None:
        """Fetch an entity by its unique Primary Key.

        Args:
            entity_id: Primary key value (typically UUID).
            options: Eager loading options (e.g. selectinload, joinedload).

        Returns:
            The ORM entity if found, otherwise None.

        Raises:
            RepositoryError: If a database error occurs.
        """
        start_time = time.perf_counter()
        logger.debug(f"Fetching {self.model.__name__} by ID: {entity_id}")
        try:
            id_column = cast(Any, self.model).id
            stmt = select(self.model).where(id_column == entity_id)
            if options:
                stmt = stmt.options(*options)
            result = await self.session.execute(stmt)
            entity = result.scalar_one_or_none()
            logger.debug(
                f"Fetched {self.model.__name__} in {time.perf_counter() - start_time:.4f}s"
            )
            return entity
        except SQLAlchemyError as exc:
            logger.error(f"Database error fetching {self.model.__name__} by ID", error=str(exc))
            raise RepositoryError(
                f"Database error fetching {self.model.__name__} by ID",
                details={"error": str(exc)},
            ) from exc

    async def get_all(
        self,
        *,
        filters: dict[str, Any] | None = None,
        sort_by: Sequence[str] | None = None,
        options: Sequence[ORMOption] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[ModelType]:
        """Fetch multiple entities applying filtering, sorting, pagination, and loading rules.

        Args:
            filters: Key-value filters. Keys representing model columns. None values are ignored.
            sort_by: Column names to sort by. Prefix column name with '-' for descending order.
            options: Eager loader options (selectinload, joinedload).
            page: Pagination page index (1-based).
            page_size: Pagination limit per page.
            limit: Standard SQL limit query override.
            offset: Standard SQL offset query override.

        Returns:
            A sequence of ORM entities.

        Raises:
            RepositoryError: If a database error occurs.
        """
        start_time = time.perf_counter()
        logger.debug(f"Querying all {self.model.__name__} records")
        try:
            stmt = select(self.model)

            # Apply loader options
            if options:
                stmt = stmt.options(*options)

            # Apply dynamic filtering (ignoring None values)
            if filters:
                clean_filters = {k: v for k, v in filters.items() if v is not None}
                # Check for is_deleted if SoftDeleteMixin applies
                stmt = stmt.filter_by(**clean_filters)

            # Apply dynamic sorting
            if sort_by:
                order_clauses = []
                for field in sort_by:
                    is_desc = field.startswith("-")
                    col_name = field[1:] if is_desc else field
                    col_attr = getattr(self.model, col_name, None)
                    if col_attr is not None:
                        order_clauses.append(col_attr.desc() if is_desc else col_attr.asc())
                if order_clauses:
                    stmt = stmt.order_by(*order_clauses)

            # Apply pagination limit/offset
            if page is not None and page_size is not None:
                calc_limit = page_size
                calc_offset = (page - 1) * page_size
                stmt = stmt.limit(calc_limit).offset(calc_offset)
            else:
                if limit is not None:
                    stmt = stmt.limit(limit)
                if offset is not None:
                    stmt = stmt.offset(offset)

            result = await self.session.execute(stmt)
            entities = result.scalars().all()
            logger.debug(
                f"Query completed, found {len(entities)} records in {time.perf_counter() - start_time:.4f}s"
            )
            return entities
        except SQLAlchemyError as exc:
            logger.error(f"Database error querying {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Failed to query {self.model.__name__} records",
                details={"error": str(exc)},
            ) from exc

    async def update(self, entity_id: Any, data: dict[str, Any] | ModelType) -> ModelType:
        """Update an existing entity by ID with dictionary values or modified ORM class.

        Args:
            entity_id: Primary key of the entity.
            data: A dictionary of fields to update, or a modified model instance.

        Returns:
            The updated ORM entity.

        Raises:
            RepositoryError: If database validations or updates fail.
        """
        start_time = time.perf_counter()
        logger.debug(f"Updating {self.model.__name__} ID: {entity_id}")
        try:
            # Retrieve active entity
            entity = await self.get_by_id(entity_id)
            if not entity:
                raise RepositoryError(
                    f"Entity {self.model.__name__} with ID '{entity_id}' not found for update"
                )

            if isinstance(data, dict):
                for key, val in data.items():
                    if hasattr(entity, key):
                        setattr(entity, key, val)
            else:
                for key in self.model.__table__.columns.keys():
                    if key != "id" and hasattr(data, key):
                        new_val = getattr(data, key)
                        setattr(entity, key, new_val)

            await self.session.flush()
            logger.debug(
                f"Successfully updated {self.model.__name__} in {time.perf_counter() - start_time:.4f}s"
            )
            return entity
        except IntegrityError as exc:
            await self.session.rollback()
            logger.error(f"Integrity violation updating {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Integrity violation updating {self.model.__name__}",
                details={"error": str(exc)},
            ) from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            logger.error(f"Database error updating {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Database error updating {self.model.__name__}",
                details={"error": str(exc)},
            ) from exc

    async def delete(self, entity_id: Any) -> bool:
        """Delete an entity by ID (performs soft-delete if model supports it).

        Args:
            entity_id: Primary key value.

        Returns:
            True if entity was found and deleted/soft-deleted, otherwise False.

        Raises:
            RepositoryError: If database delete operations fail.
        """
        start_time = time.perf_counter()
        logger.debug(f"Deleting {self.model.__name__} ID: {entity_id}")
        try:
            entity = await self.get_by_id(entity_id)
            if not entity:
                logger.debug(f"Entity {self.model.__name__} ID {entity_id} not found for deletion")
                return False

            # Check if model has soft-delete capability
            if hasattr(entity, "is_deleted") and hasattr(entity, "soft_delete"):
                entity.soft_delete()
                logger.debug(f"Performed soft-delete on {self.model.__name__} ID {entity_id}")
            else:
                await self.session.delete(entity)
                logger.debug(f"Performed hard-delete on {self.model.__name__} ID {entity_id}")

            await self.session.flush()
            logger.debug(
                f"Deleted {self.model.__name__} in {time.perf_counter() - start_time:.4f}s"
            )
            return True
        except SQLAlchemyError as exc:
            await self.session.rollback()
            logger.error(f"Database error deleting {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Failed to delete {self.model.__name__} entity",
                details={"error": str(exc)},
            ) from exc

    async def hard_delete(self, entity_id: Any) -> bool:
        """Force delete a record from the database.

        Args:
            entity_id: Primary key value.

        Returns:
            True if entity was found and deleted, otherwise False.

        Raises:
            RepositoryError: If delete operations fail.
        """
        start_time = time.perf_counter()
        logger.debug(f"Hard deleting {self.model.__name__} ID: {entity_id}")
        try:
            entity = await self.get_by_id(entity_id)
            if not entity:
                return False

            await self.session.delete(entity)
            await self.session.flush()
            logger.debug(
                f"Hard deleted {self.model.__name__} in {time.perf_counter() - start_time:.4f}s"
            )
            return True
        except SQLAlchemyError as exc:
            await self.session.rollback()
            logger.error(f"Database error hard deleting {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Failed to hard delete {self.model.__name__} entity",
                details={"error": str(exc)},
            ) from exc

    async def exists(self, **filters: Any) -> bool:
        """Check if any entity matches the provided filters.

        Args:
            filters: Field values to match.

        Returns:
            True if matching record exists, False otherwise.

        Raises:
            RepositoryError: If database search fails.
        """
        try:
            
            id_column = cast(Any, self.model).id
            stmt = select(id_column).filter_by(**filters)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as exc:
            logger.error(f"Database error checking existence of {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Failed to check existence of {self.model.__name__}",
                details={"error": str(exc)},
            ) from exc

    async def count(self, **filters: Any) -> int:
        """Count the total number of entities matching filters.

        Args:
            filters: Field values to match.

        Returns:
            Integer count of matching database rows.

        Raises:
            RepositoryError: If count query fails.
        """
        try:
            stmt = select(func.count()).select_from(self.model).filter_by(**filters)
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as exc:
            logger.error(f"Database error counting {self.model.__name__}", error=str(exc))
            raise RepositoryError(
                f"Failed to count {self.model.__name__} records",
                details={"error": str(exc)},
            ) from exc

    # Search Helpers (Reusable query extensions)
    async def get_by_field(
        self,
        field_name: str,
        value: Any,
        options: Sequence[ORMOption] | None = None,
    ) -> ModelType | None:
        """Fetch a single record by matching a specific field value.

        Args:
            field_name: Column name on the model.
            value: Value to look up.
            options: Eager loading options.

        Returns:
            Matching ORM record or None.
        """
        filters = {field_name: value}
        records = await self.get_all(filters=filters, options=options, limit=1)
        return records[0] if records else None

    async def get_one_by(
        self,
        filters: dict[str, Any],
        options: Sequence[ORMOption] | None = None,
    ) -> ModelType | None:
        """Fetch a single record by matching multiple criteria.

        Args:
            filters: Key-value search filters.
            options: Eager loading options.

        Returns:
            Matching record or None.
        """
        records = await self.get_all(filters=filters, options=options, limit=1)
        return records[0] if records else None

    async def get_many_by(
        self,
        filters: dict[str, Any],
        *,
        sort_by: Sequence[str] | None = None,
        options: Sequence[ORMOption] | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> Sequence[ModelType]:
        """Fetch multiple records matching criteria with sorting and pagination support.

        Args:
            filters: Key-value search filters.
            sort_by: Sorting keys.
            options: Eager loading options.
            page: 1-based page.
            page_size: limit per page.

        Returns:
            A sequence of ORM models.
        """
        return await self.get_all(
            filters=filters,
            sort_by=sort_by,
            options=options,
            page=page,
            page_size=page_size,
        )

    # Database Session Transaction methods
    async def flush(self) -> None:
        """Flush pending transactional changes to the database."""
        try:
            await self.session.flush()
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise RepositoryError(
                "Database error during flush operation", details={"error": str(exc)}
            ) from exc

    async def refresh(self, entity: ModelType) -> None:
        """Refresh object attributes from the database.

        Args:
            entity: ORM entity in the active session.
        """
        try:
            await self.session.refresh(entity)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                "Database error during refresh operation", details={"error": str(exc)}
            ) from exc

    async def commit(self) -> None:
        """Commit the active database transaction."""
        try:
            await self.session.commit()
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise RepositoryError(
                "Database error during commit transaction", details={"error": str(exc)}
            ) from exc

    async def rollback(self) -> None:
        """Roll back the active database transaction."""
        try:
            await self.session.rollback()
        except SQLAlchemyError as exc:
            raise RepositoryError(
                "Database error during transaction rollback", details={"error": str(exc)}
            ) from exc
