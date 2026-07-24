"""PostgreSQL implementation of ProductRepositoryInterface."""

import uuid
from datetime import UTC, datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import RepositoryError
from src.domain.models.product import Product
from src.interfaces.repository import ProductRepositoryInterface
from src.orm.models import ImageORM, PriceHistoryORM, ProductFingerprintORM, ProductORM, SpecificationORM
from src.mappers.product import domain_to_orm, orm_to_domain


class PostgresProductRepository(ProductRepositoryInterface):
    """Async PostgreSQL Product Repository handling product domain model persistence."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize PostgresProductRepository with an active database session."""
        self.session = session

    async def get_by_id(self, entity_id: str) -> Product | None:
        """Fetch Product by unique UUID ID."""
        try:
            stmt = (
                select(ProductORM)
                .options(
                    selectinload(ProductORM.specs),
                    selectinload(ProductORM.price_history),
                    selectinload(ProductORM.images),
                    selectinload(ProductORM.fingerprint),
                )
                .where(ProductORM.id == entity_id)
            )
            result = await self.session.execute(stmt)
            orm = result.scalar_one_or_none()
            return orm_to_domain(orm) if orm else None
        except Exception as exc:
            raise RepositoryError(
                f"Error retrieving product by id {entity_id}", details={"error": str(exc)}
            ) from exc

    async def get_by_url(self, url: str) -> Product | None:
        """Retrieve Product by canonical page URL."""
        try:
            stmt = (
                select(ProductORM)
                .options(
                    selectinload(ProductORM.specs),
                    selectinload(ProductORM.price_history),
                    selectinload(ProductORM.images),
                    selectinload(ProductORM.fingerprint),
                )
                .where(ProductORM.url == url)
            )
            result = await self.session.execute(stmt)
            orm = result.scalar_one_or_none()
            return orm_to_domain(orm) if orm else None
        except Exception as exc:
            raise RepositoryError(
                f"Error retrieving product by url {url}", details={"error": str(exc)}
            ) from exc

    async def get_by_fingerprint(self, hash_key: str) -> Product | None:
        """Retrieve Product by duplicate detection fingerprint hash key."""
        try:
            stmt = (
                select(ProductORM)
                .join(ProductFingerprintORM)
                .options(
                    selectinload(ProductORM.specs),
                    selectinload(ProductORM.price_history),
                    selectinload(ProductORM.images),
                    selectinload(ProductORM.fingerprint),
                )
                .where(ProductFingerprintORM.hash_key == hash_key)
            )
            result = await self.session.execute(stmt)
            orm = result.scalar_one_or_none()
            return orm_to_domain(orm) if orm else None
        except Exception as exc:
            raise RepositoryError(
                f"Error retrieving product by fingerprint {hash_key}", details={"error": str(exc)}
            ) from exc

    async def save(self, entity: Product) -> Product:
        """Save product entity via upsert logic."""
        if not entity.id:
            entity.id = str(uuid.uuid4())
        return await self.upsert(entity)

    async def update(self, product: Product) -> Product:
        """Update an existing product listing."""
        if not product.id:
            raise ValueError("Product must have a valid ID to be updated")

        try:
            stmt = select(ProductORM).where(ProductORM.id == product.id)
            res = await self.session.execute(stmt)
            orm = res.scalar_one_or_none()
            if not orm:
                raise ValueError(f"Product with ID '{product.id}' not found for update")

            # Update the direct fields
            orm.current_price = product.current_price
            orm.original_price = product.original_price
            orm.is_in_stock = product.is_in_stock
            orm.rating = product.rating
            orm.review_count = product.review_count
            orm.raw_payload_id = product.raw_payload_id
            orm.metadata_json = product.metadata or {}
            orm.updated_at = datetime.now(UTC)

            # Update specs attributes
            if orm.specs:
                specs_dict = product.specs.model_dump() if product.specs else {}
                orm.specs.attributes = specs_dict.get("attributes", specs_dict)
                orm.specs.updated_at = datetime.now(UTC)

            # Replace images
            # Clear old images
            stmt_images = select(ImageORM).where(ImageORM.product_id == orm.id)
            res_images = await self.session.execute(stmt_images)
            for img in res_images.scalars():
                await self.session.delete(img)

            # Add new images
            for url in product.image_urls:
                self.session.add(ImageORM(product_id=orm.id, url=url))

            # Add PriceHistory record
            price_history_entry = PriceHistoryORM(
                product_id=orm.id,
                price=product.current_price,
                original_price=product.original_price,
                currency=product.currency.value,
                is_in_stock=product.is_in_stock,
                timestamp=datetime.now(UTC),
            )
            self.session.add(price_history_entry)

            # Update fingerprint if changed
            if product.fingerprint:
                if orm.fingerprint:
                    orm.fingerprint.hash_key = product.fingerprint.hash_key
                    orm.fingerprint.brand = product.fingerprint.brand
                    orm.fingerprint.normalized_model = product.fingerprint.normalized_model
                    orm.fingerprint.category = product.fingerprint.category.value
                    orm.fingerprint.updated_at = datetime.now(UTC)
                else:
                    orm.fingerprint = ProductFingerprintORM(
                        product_id=orm.id,
                        hash_key=product.fingerprint.hash_key,
                        brand=product.fingerprint.brand,
                        normalized_model=product.fingerprint.normalized_model,
                        category=product.fingerprint.category.value,
                    )

            await self.session.flush()
            # Return updated domain
            updated_orm = await self.session.execute(
                select(ProductORM)
                .options(
                    selectinload(ProductORM.specs),
                    selectinload(ProductORM.price_history),
                    selectinload(ProductORM.images),
                    selectinload(ProductORM.fingerprint),
                )
                .where(ProductORM.id == orm.id)
            )
            return orm_to_domain(updated_orm.scalar_one())
        except Exception as exc:
            raise RepositoryError(
                f"Failed to update product with ID {product.id}", details={"error": str(exc)}
            ) from exc

    async def delete(self, entity_id: str) -> bool:
        """Delete Product by ID."""
        try:
            stmt = select(ProductORM).where(ProductORM.id == entity_id)
            res = await self.session.execute(stmt)
            orm = res.scalar_one_or_none()
            if orm:
                await self.session.delete(orm)
                await self.session.flush()
                return True
            return False
        except Exception as exc:
            raise RepositoryError(
                f"Failed to delete product {entity_id}", details={"error": str(exc)}
            ) from exc

    async def find_by_id(self, entity_id: str) -> Product | None:
        """Find Product by unique ID."""
        return await self.get_by_id(entity_id)

    async def find_by_url(self, url: str) -> Product | None:
        """Find Product by URL."""
        return await self.get_by_url(url)

    async def exists(self, entity_id: str) -> bool:
        """Check if Product exists by ID."""
        try:
            stmt = select(ProductORM.id).where(ProductORM.id == entity_id)
            res = await self.session.execute(stmt)
            return res.scalar_one_or_none() is not None
        except Exception as exc:
            raise RepositoryError(
                f"Failed to check existence for product ID {entity_id}", details={"error": str(exc)}
            ) from exc

    async def list(self) -> list[Product]:
        """List all products in the database."""
        try:
            stmt = select(ProductORM).options(
                selectinload(ProductORM.specs),
                selectinload(ProductORM.price_history),
                selectinload(ProductORM.images),
                selectinload(ProductORM.fingerprint),
            )
            res = await self.session.execute(stmt)
            return [orm_to_domain(orm) for orm in res.scalars()]
        except Exception as exc:
            raise RepositoryError("Failed to list products from database", details={"error": str(exc)}) from exc

    async def count(self) -> int:
        """Return total count of products in database."""
        try:
            stmt = select(func.count(ProductORM.id))
            res = await self.session.execute(stmt)
            return res.scalar() or 0
        except Exception as exc:
            raise RepositoryError("Failed to count products in database", details={"error": str(exc)}) from exc

    async def upsert(self, product: Product) -> Product:
        """Insert product or update listing dynamically based on URL/fingerprint match."""
        return await self.upsert_product(product)

    async def upsert_product(self, product: Product) -> Product:
        """Atomic upsert inserting new product or updating price & specs if existing."""
        try:
            existing = await self.get_by_url(product.url)
            if not existing and product.fingerprint:
                existing = await self.get_by_fingerprint(product.fingerprint.hash_key)

            if existing and existing.id:
                product.id = existing.id
                return await self.update(product)
            else:
                # Insert new ORM
                if not product.id:
                    product.id = str(uuid.uuid4())
                orm = domain_to_orm(product)
                self.session.add(orm)
                await self.session.flush()

                # Re-fetch full domain model with eager relationships
                saved = await self.get_by_id(orm.id)
                return saved or product

        except Exception as exc:
            raise RepositoryError(
                f"Failed to upsert product {product.url}", details={"error": str(exc)}
            ) from exc

    async def bulk_insert(self, products: list[Product]) -> list[Product]:
        """Bulk insert multiple products. Wraps in single transaction."""
        inserted_products = []
        try:
            for product in products:
                if not product.id:
                    product.id = str(uuid.uuid4())
                orm = domain_to_orm(product)
                self.session.add(orm)
                inserted_products.append(orm)
            await self.session.flush()

            # Return domain list
            stmt = (
                select(ProductORM)
                .options(
                    selectinload(ProductORM.specs),
                    selectinload(ProductORM.price_history),
                    selectinload(ProductORM.images),
                    selectinload(ProductORM.fingerprint),
                )
                .where(ProductORM.id.in_([orm.id for orm in inserted_products]))
            )
            res = await self.session.execute(stmt)
            return [orm_to_domain(orm) for orm in res.scalars()]
        except Exception as exc:
            raise RepositoryError("Failed to bulk insert products", details={"error": str(exc)}) from exc

    async def bulk_upsert(self, products: list[Product]) -> list[Product]:
        """Bulk upsert multiple products, avoiding duplicates."""
        upserted_products = []
        try:
            for product in products:
                up_p = await self.upsert(product)
                upserted_products.append(up_p)
            return upserted_products
        except Exception as exc:
            raise RepositoryError("Failed to bulk upsert products", details={"error": str(exc)}) from exc
