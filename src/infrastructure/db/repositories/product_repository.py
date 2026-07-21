"""SQLAlchemy implementation of ProductRepositoryInterface."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import RepositoryError
from src.core.logging import get_logger
from src.domain.enums import CategoryEnum, CurrencyEnum
from src.domain.models.product import PriceHistory, Product, ProductFingerprint
from src.domain.models.specs import GenericProductSpecs, LaptopSpecs, MobileSpecs
from src.infrastructure.db.models.product import (
    PriceHistoryORM,
    ProductFingerprintORM,
    ProductORM,
    ProductSpecORM,
)
from src.infrastructure.db.repositories.base import BaseSQLAlchemyRepository
from src.interfaces.repository import ProductRepositoryInterface

logger = get_logger(__name__)


class ProductRepository(BaseSQLAlchemyRepository[Product], ProductRepositoryInterface):
    """Async SQLAlchemy Product Repository handling product domain model persistence."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_id(self, entity_id: str) -> Product | None:
        """Fetch Product by unique UUID ID."""
        try:
            stmt = (
                select(ProductORM)
                .options(
                    selectinload(ProductORM.specs),
                    selectinload(ProductORM.price_history),
                    selectinload(ProductORM.fingerprint),
                )
                .where(ProductORM.id == entity_id)
            )
            result = await self.session.execute(stmt)
            orm = result.scalar_one_or_none()
            return self._to_domain(orm) if orm else None
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
                    selectinload(ProductORM.fingerprint),
                )
                .where(ProductORM.url == url)
            )
            result = await self.session.execute(stmt)
            orm = result.scalar_one_or_none()
            return self._to_domain(orm) if orm else None
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
                    selectinload(ProductORM.fingerprint),
                )
                .where(ProductFingerprintORM.hash_key == hash_key)
            )
            result = await self.session.execute(stmt)
            orm = result.scalar_one_or_none()
            return self._to_domain(orm) if orm else None
        except Exception as exc:
            raise RepositoryError(
                f"Error retrieving product by fingerprint {hash_key}", details={"error": str(exc)}
            ) from exc

    async def save(self, entity: Product) -> Product:
        """Save product entity via upsert logic."""
        return await self.upsert_product(entity)

    async def upsert_product(self, product: Product) -> Product:
        """Atomic upsert inserting new product or updating price & specs if existing."""
        try:
            existing = await self.get_by_url(product.url)
            if not existing and product.fingerprint:
                existing = await self.get_by_fingerprint(product.fingerprint.hash_key)

            if existing and existing.id:
                # Update existing ORM
                stmt = select(ProductORM).where(ProductORM.id == existing.id)
                res = await self.session.execute(stmt)
                orm = res.scalar_one()

                orm.current_price = product.current_price
                orm.original_price = product.original_price
                orm.is_in_stock = product.is_in_stock
                orm.rating = product.rating
                orm.review_count = product.review_count
                orm.image_urls = product.image_urls
                orm.updated_at = datetime.now(UTC)

                # Append new price history entry
                price_history_entry = PriceHistoryORM(
                    product_id=orm.id,
                    price=product.current_price,
                    original_price=product.original_price,
                    currency=product.currency.value,
                    is_in_stock=product.is_in_stock,
                )
                self.session.add(price_history_entry)

                await self.session.flush()
                return self._to_domain(orm)
            else:
                # Insert new ORM
                orm = ProductORM(
                    site_id=product.site_id,
                    url=product.url,
                    sku=product.sku,
                    title=product.title,
                    brand=product.brand,
                    model_name=product.model_name,
                    category=product.category.value,
                    current_price=product.current_price,
                    original_price=product.original_price,
                    currency=product.currency.value,
                    is_in_stock=product.is_in_stock,
                    rating=product.rating,
                    review_count=product.review_count,
                    image_urls=product.image_urls,
                    raw_payload_id=product.raw_payload_id,
                    metadata_json=product.metadata,
                )
                self.session.add(orm)
                await self.session.flush()

                # Add Specs
                specs_dict = product.specs.model_dump()
                specs_orm = ProductSpecORM(product_id=orm.id, attributes=specs_dict)
                self.session.add(specs_orm)

                # Add Initial Price History
                price_history_orm = PriceHistoryORM(
                    product_id=orm.id,
                    price=product.current_price,
                    original_price=product.original_price,
                    currency=product.currency.value,
                    is_in_stock=product.is_in_stock,
                )
                self.session.add(price_history_orm)

                # Add Fingerprint if present
                if product.fingerprint:
                    fp_orm = ProductFingerprintORM(
                        product_id=orm.id,
                        hash_key=product.fingerprint.hash_key,
                        brand=product.fingerprint.brand,
                        normalized_model=product.fingerprint.normalized_model,
                        category=product.fingerprint.category.value,
                    )
                    self.session.add(fp_orm)

                await self.session.flush()
                # Re-fetch full domain model with eager relationships
                saved = await self.get_by_id(orm.id)
                return saved or product

        except Exception as exc:
            raise RepositoryError(
                f"Failed to upsert product {product.url}", details={"error": str(exc)}
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

    def _to_domain(self, orm: ProductORM) -> Product:
        """Map SQLAlchemy ProductORM to Product domain model."""
        category = CategoryEnum(orm.category)

        # Map specs
        specs_attrs = orm.specs.attributes if orm.specs else {}
        specs: LaptopSpecs | MobileSpecs | GenericProductSpecs
        if category == CategoryEnum.LAPTOP:
            specs = LaptopSpecs.model_validate(specs_attrs)
        elif category == CategoryEnum.MOBILE:
            specs = MobileSpecs.model_validate(specs_attrs)
        else:
            specs = GenericProductSpecs.model_validate({"attributes": specs_attrs})

        # Map price history
        history = [
            PriceHistory(
                id=ph.id,
                product_id=ph.product_id,
                price=ph.price,
                original_price=ph.original_price,
                currency=CurrencyEnum(ph.currency),
                is_in_stock=ph.is_in_stock,
                seller_name=ph.seller_name,
                timestamp=ph.created_at,
            )
            for ph in (orm.price_history or [])
        ]

        # Map fingerprint
        fingerprint = None
        if orm.fingerprint:
            fingerprint = ProductFingerprint(
                hash_key=orm.fingerprint.hash_key,
                brand=orm.fingerprint.brand,
                normalized_model=orm.fingerprint.normalized_model,
                category=CategoryEnum(orm.fingerprint.category),
            )

        return Product(
            id=orm.id,
            site_id=orm.site_id,
            url=orm.url,
            sku=orm.sku,
            title=orm.title,
            brand=orm.brand,
            model_name=orm.model_name,
            category=category,
            current_price=orm.current_price,
            original_price=orm.original_price,
            currency=CurrencyEnum(orm.currency),
            is_in_stock=orm.is_in_stock,
            rating=orm.rating,
            review_count=orm.review_count,
            image_urls=orm.image_urls or [],
            raw_payload_id=orm.raw_payload_id,
            specs=specs,
            price_history=history,
            fingerprint=fingerprint,
            metadata=orm.metadata_json or {},
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )
