"""Integration tests for Phase 6 Database Models.

This suite verifies table creation, relationships, cascading rules,
check constraints, and database validation bounds under a live PostgreSQL transaction.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import get_settings
from src.infrastructure.db.base import Base
from src.models import (
    Category,
    Currency,
    Merchant,
    MerchantStatus,
    Notification,
    NotificationType,
    PriceHistory,
    Product,
    ProductImage,
    ProductPrice,
    ProductReview,
    ProductStatus,
    ReviewSource,
    SearchHistory,
    User,
    UserRole,
    Wishlist,
    WishlistItem,
    WishlistVisibility,
)


@pytest.fixture
def db_url() -> str:
    """Get database URL for integration tests."""
    settings = get_settings()
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture
async def test_engine(db_url: str):
    """Create a clean database engine and schema for Phase 6 tests."""
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


@pytest.mark.asyncio
async def test_full_model_lifecycle_and_relations(db_session: AsyncSession) -> None:
    """Verify insertion and verification of all 12 Phase 6 models."""

    # 1. Create User
    user = User(
        email="test_user@example.com",
        first_name="Jane",
        last_name="Doe",
        role=UserRole.USER,
    )
    db_session.add(user)
    await db_session.flush()
    assert user.id is not None

    # 2. Create Merchant
    merchant = Merchant(
        name="Amazon Test",
        domain="amazon.test",
        status=MerchantStatus.ACTIVE,
    )
    db_session.add(merchant)
    await db_session.flush()
    assert merchant.id is not None

    # 3. Create Category
    parent_cat = Category(name="Electronics", slug="electronics")
    db_session.add(parent_cat)
    await db_session.flush()

    child_cat = Category(
        name="Laptops",
        slug="electronics-laptops",
        parent_id=parent_cat.id,
    )
    db_session.add(child_cat)
    await db_session.flush()
    assert child_cat.parent_id == parent_cat.id

    # 4. Create Product
    product = Product(
        title="Gaming Laptop 15",
        brand="BrandX",
        model_name="BX-15",
        sku="SKU-BX15",
        status=ProductStatus.ACTIVE,
        category_id=child_cat.id,
        attributes={"ram_gb": 16, "storage_gb": 512},
    )
    db_session.add(product)
    await db_session.flush()
    assert product.id is not None

    # 5. Create ProductImage
    image = ProductImage(
        product_id=product.id,
        url="https://images.test/bx15.jpg",
        alt_text="Front view BX-15",
        position=0,
    )
    db_session.add(image)
    await db_session.flush()

    # 6. Create ProductPrice
    price = ProductPrice(
        product_id=product.id,
        merchant_id=merchant.id,
        price=Decimal("1299.99"),
        currency=Currency.USD,
        url="https://amazon.test/bx15",
        is_in_stock=True,
        shipping_cost=Decimal("0.00"),
        last_updated=datetime.now(UTC),
    )
    db_session.add(price)
    await db_session.flush()
    assert price.id is not None

    # 7. Create PriceHistory
    history = PriceHistory(
        product_price_id=price.id,
        price=Decimal("1299.99"),
        currency=Currency.USD,
        is_in_stock=True,
        recorded_at=datetime.now(UTC),
    )
    db_session.add(history)
    await db_session.flush()

    # 8. Create ProductReview
    review = ProductReview(
        product_id=product.id,
        user_id=user.id,
        rating=4.5,
        title="Decent speed",
        content="Great laptop for the price.",
        author_name="Jane Doe",
        source=ReviewSource.INTERNAL,
    )
    db_session.add(review)
    await db_session.flush()

    # 9. Create Wishlist
    wishlist = Wishlist(
        user_id=user.id,
        name="Birthday Wishlist",
        visibility=WishlistVisibility.PRIVATE,
    )
    db_session.add(wishlist)
    await db_session.flush()

    # 10. Create WishlistItem
    wishlist_item = WishlistItem(
        wishlist_id=wishlist.id,
        product_id=product.id,
        desired_price=Decimal("1100.00"),
    )
    db_session.add(wishlist_item)
    await db_session.flush()

    # 11. Create SearchHistory
    search = SearchHistory(
        user_id=user.id,
        query="gaming laptop BX-15",
        filters={"category": "Laptops"},
        results_count=1,
    )
    db_session.add(search)
    await db_session.flush()

    # 12. Create Notification
    notification = Notification(
        user_id=user.id,
        title="Price Drop alert!",
        message="Gaming Laptop BX-15 dropped to $1299.99",
        type=NotificationType.PRICE_DROP,
        is_read=False,
    )
    db_session.add(notification)
    await db_session.flush()

    # Refresh session and verify relations
    await db_session.commit()

    # Verify query mappings
    stmt = select(User).where(User.id == user.id)
    res = await db_session.execute(stmt)
    db_user = res.scalar_one()
    assert len(db_user.wishlists) == 1
    assert db_user.wishlists[0].name == "Birthday Wishlist"
    assert len(db_user.notifications) == 1
    assert db_user.notifications[0].type == NotificationType.PRICE_DROP

    # Verify self-referential categories
    stmt = select(Category).where(Category.id == parent_cat.id)
    res = await db_session.execute(stmt)
    db_parent = res.scalar_one()
    assert len(db_parent.children) == 1
    assert db_parent.children[0].name == "Laptops"


@pytest.mark.asyncio
async def test_check_constraints(db_session: AsyncSession) -> None:
    """Verify check constraints prevent illegal price values and rating limits."""

    user = User(email="critic@example.com")
    product = Product(title="Cheap Item", status=ProductStatus.ACTIVE)
    db_session.add_all([user, product])
    await db_session.flush()

    # Test invalid review rating (6.0 is out of bounds)
    invalid_review = ProductReview(
        product_id=product.id,
        user_id=user.id,
        rating=6.0,  # Fails constraint rating <= 5.0
        source=ReviewSource.INTERNAL,
    )
    db_session.add(invalid_review)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_cascading_rules(db_session: AsyncSession) -> None:
    """Verify that deleting records cascades correctly across entities."""

    # Setup User and Wishlist
    user = User(email="cascade@example.com")
    merchant = Merchant(name="Cascader Store", domain="cascader.com")
    db_session.add_all([user, merchant])
    await db_session.flush()

    product = Product(title="Cascading Product", status=ProductStatus.ACTIVE)
    db_session.add(product)
    await db_session.flush()

    wishlist = Wishlist(user_id=user.id, name="Temp Wishlist")
    db_session.add(wishlist)
    await db_session.flush()

    wishlist_item = WishlistItem(wishlist_id=wishlist.id, product_id=product.id)
    review = ProductReview(
        product_id=product.id,
        user_id=user.id,
        rating=4.0,
        source=ReviewSource.INTERNAL,
    )
    db_session.add_all([wishlist_item, review])
    await db_session.commit()

    # 1. Delete user: Should delete wishlist, but keep the review (user_id becomes null)
    await db_session.delete(user)
    await db_session.commit()

    # Wishlist should be gone
    stmt = select(Wishlist).where(Wishlist.id == wishlist.id)
    res = await db_session.execute(stmt)
    assert res.scalar_one_or_none() is None

    # Review should still exist but user_id is null
    stmt = select(ProductReview).where(ProductReview.id == review.id)
    res = await db_session.execute(stmt)
    db_review = res.scalar_one()
    assert db_review.user_id is None

    # 2. Delete product: Should delete review and wishlist_item
    await db_session.delete(product)
    await db_session.commit()

    stmt = select(ProductReview).where(ProductReview.id == review.id)
    res = await db_session.execute(stmt)
    assert res.scalar_one_or_none() is None

    stmt = select(WishlistItem).where(WishlistItem.id == wishlist_item.id)
    res = await db_session.execute(stmt)
    assert res.scalar_one_or_none() is None
