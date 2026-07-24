"""Integration tests for PostgresProductRepository."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.database.base import Base
from src.domain.enums import CategoryEnum, CurrencyEnum
from src.domain.models.product import Product, PriceHistory, ProductFingerprint
from src.domain.models.specs import LaptopSpecs
from src.repositories.postgres.product import PostgresProductRepository
from src.config.settings import get_settings
from src.orm.models import ProductORM


@pytest.fixture(scope="module")
def db_url() -> str:
    """Get database URL for integration tests."""
    settings = get_settings()
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture(scope="module")
async def test_engine(db_url: str):
    """Create a clean database engine and schema for tests."""
    engine = create_async_engine(db_url, echo=False)
    # Recreate tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # Cleanup tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    """Create an AsyncSession with automatic rollback after test completes."""
    session_maker = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def product_factory():
    """Factory to create a valid Product domain model for testing."""
    def _create(sku: str = "sku-123", url: str = "https://example.com/p1") -> Product:
        return Product(
            site_id="amazon_us",
            url=url,
            sku=sku,
            title="iPhone 15 Pro",
            brand="Apple",
            model_name="iPhone 15 Pro",
            category=CategoryEnum.MOBILE,
            current_price=999.00,
            original_price=1099.00,
            currency=CurrencyEnum.USD,
            is_in_stock=True,
            rating=4.8,
            review_count=1500,
            image_urls=["https://images.com/iphone15.jpg"],
            specs=LaptopSpecs(
                processor="A17 Pro",
                ram_gb=8,
                storage_gb=128,
            ),
            fingerprint=ProductFingerprint.generate(
                brand="Apple",
                model="iPhone 15 Pro",
                category=CategoryEnum.MOBILE,
            ),
        )
    return _create


@pytest.mark.asyncio
async def test_insert_and_find_by_id(db_session: AsyncSession, product_factory) -> None:
    """Verify product insertion and retrieval by ID."""
    repo = PostgresProductRepository(db_session)
    product = product_factory()

    saved = await repo.save(product)
    assert saved.id is not None

    fetched = await repo.find_by_id(saved.id)
    assert fetched is not None
    assert fetched.id == saved.id
    assert fetched.title == "iPhone 15 Pro"
    assert len(fetched.price_history) == 1
    assert fetched.price_history[0].price == 999.00
    assert len(fetched.image_urls) == 1
    assert fetched.image_urls[0] == "https://images.com/iphone15.jpg"
    assert fetched.fingerprint is not None
    assert fetched.fingerprint.brand == "apple"


@pytest.mark.asyncio
async def test_update_product(db_session: AsyncSession, product_factory) -> None:
    """Verify product update operations."""
    repo = PostgresProductRepository(db_session)
    product = product_factory()

    saved = await repo.save(product)
    assert saved.id is not None

    # Modify properties
    saved.title = "iPhone 15 Pro Max"
    saved.current_price = 1199.00
    saved.image_urls.append("https://images.com/iphone15_back.jpg")

    updated = await repo.update(saved)
    assert updated.title == "iPhone 15 Pro Max"
    assert updated.current_price == 1199.00
    assert len(updated.image_urls) == 2

    # Check price history is appended
    fetched = await repo.find_by_id(saved.id)
    assert fetched is not None
    assert len(fetched.price_history) == 2


@pytest.mark.asyncio
async def test_delete_product(db_session: AsyncSession, product_factory) -> None:
    """Verify product deletion operations."""
    repo = PostgresProductRepository(db_session)
    product = product_factory()

    saved = await repo.save(product)
    assert await repo.exists(saved.id) is True

    deleted = await repo.delete(saved.id)
    assert deleted is True
    assert await repo.exists(saved.id) is False


@pytest.mark.asyncio
async def test_find_by_url(db_session: AsyncSession, product_factory) -> None:
    """Verify retrieval by canonical URL."""
    repo = PostgresProductRepository(db_session)
    product = product_factory(url="https://example.com/unique-url")

    saved = await repo.save(product)
    fetched = await repo.find_by_url("https://example.com/unique-url")
    assert fetched is not None
    assert fetched.id == saved.id


@pytest.mark.asyncio
async def test_exists(db_session: AsyncSession, product_factory) -> None:
    """Verify exist check method."""
    repo = PostgresProductRepository(db_session)
    product = product_factory()
    saved = await repo.save(product)
    assert await repo.exists(saved.id) is True
    assert await repo.exists("non-existent-id") is False


@pytest.mark.asyncio
async def test_list_and_count(db_session: AsyncSession, product_factory) -> None:
    """Verify repository list and count operations."""
    repo = PostgresProductRepository(db_session)

    p1 = product_factory(sku="sku-1", url="https://example.com/p1")
    p2 = product_factory(sku="sku-2", url="https://example.com/p2")

    await repo.save(p1)
    await repo.save(p2)

    assert await repo.count() == 2
    items = await repo.list()
    assert len(items) == 2


@pytest.mark.asyncio
async def test_bulk_insert(db_session: AsyncSession, product_factory) -> None:
    """Verify bulk insert behavior."""
    repo = PostgresProductRepository(db_session)

    p1 = product_factory(sku="sku-1", url="https://example.com/p1")
    p2 = product_factory(sku="sku-2", url="https://example.com/p2")

    inserted = await repo.bulk_insert([p1, p2])
    assert len(inserted) == 2
    assert inserted[0].id is not None
    assert inserted[1].id is not None


@pytest.mark.asyncio
async def test_bulk_upsert(db_session: AsyncSession, product_factory) -> None:
    """Verify bulk upsert behavior handles inserts and updates."""
    repo = PostgresProductRepository(db_session)

    p1 = product_factory(sku="sku-1", url="https://example.com/p1")
    saved_p1 = await repo.save(p1)

    # Prepare list containing an update and a new insert
    saved_p1.current_price = 899.00
    p2 = product_factory(sku="sku-2", url="https://example.com/p2")

    upserted = await repo.bulk_upsert([saved_p1, p2])
    assert len(upserted) == 2

    # Verify update
    p1_fetched = await repo.find_by_id(saved_p1.id)
    assert p1_fetched is not None
    assert p1_fetched.current_price == 899.00

    # Verify insert
    assert await repo.count() == 2


@pytest.mark.asyncio
async def test_transaction_rollback(test_engine, db_url) -> None:
    """Verify that transactions are rolled back properly on failure."""
    session_maker = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    # Insert a product and commit
    async with session_maker() as session:
        repo = PostgresProductRepository(session)
        p = Product(
            site_id="amazon_us",
            url="https://example.com/rollback-test",
            title="Rollback Test Product",
            brand="Test",
            model_name="Rollback-1",
            category=CategoryEnum.MOBILE,
            current_price=100.00,
        )
        saved = await repo.save(p)
        await session.commit()
        product_id = saved.id

    # Verify committed
    async with session_maker() as session:
        stmt = select(ProductORM).where(ProductORM.id == product_id)
        res = await session.execute(stmt)
        assert res.scalar_one_or_none() is not None

    # Start a session, perform updates, but cause an error and rollback
    async with session_maker() as session:
        repo = PostgresProductRepository(session)
        fetched = await repo.find_by_id(product_id)
        assert fetched is not None
        fetched.title = "Updated Title"
        await repo.update(fetched)

        # Force a rollback
        await session.rollback()

    # Verify update did NOT persist
    async with session_maker() as session:
        repo = PostgresProductRepository(session)
        fetched = await repo.find_by_id(product_id)
        assert fetched is not None
        assert fetched.title == "Rollback Test Product"

    # Clean up the test product
    async with session_maker() as session:
        repo = PostgresProductRepository(session)
        await repo.delete(product_id)
        await session.commit()
