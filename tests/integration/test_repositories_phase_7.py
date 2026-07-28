"""Integration tests for Phase 7 Repository Layer.

Verifies generic BaseRepository operations, filtering, pagination, sorting,
soft delete capabilities, and all custom repository queries under active DB transactions.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import get_settings
from src.core.exceptions import RepositoryError
from src.infrastructure.db.base import Base
from src.models import (
    Category,
    Merchant,
    Notification,
    NotificationType,
    PriceHistory,
    Product,
    ProductPrice,
    ProductReview,
    ProductStatus,
    ReviewSource,
    User,
    UserRole,
    Wishlist,
)
from src.repositories import (
    CategoryRepository,
    MerchantRepository,
    NotificationRepository,
    PriceHistoryRepository,
    ProductPriceRepository,
    ProductRepository,
    ProductReviewRepository,
    UserRepository,
    WishlistItemRepository,
    WishlistRepository,
)


@pytest.fixture
def db_url() -> str:
    """Get database connection string."""
    settings = get_settings()
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture
async def test_engine(db_url: str):
    """Recreate clean database tables for testing."""
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    """Provide a transactional session automatically rolled back after each test."""
    session_maker = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_base_repository_generic_crud(db_session: AsyncSession) -> None:
    """Verify generic base repository operations including dynamic filtering, pagination, and soft delete."""
    user_repo = UserRepository(db_session)

    # 1. Create
    u1 = User(email="rep_u1@example.com", role=UserRole.USER)
    u2 = User(email="rep_u2@example.com", role=UserRole.USER)
    await user_repo.create(u1)
    await user_repo.create(u2)

    # 2. Get by ID
    fetched_u1 = await user_repo.get_by_id(u1.id)
    assert fetched_u1 is not None
    assert fetched_u1.email == "rep_u1@example.com"

    # 3. Dynamic Filter & List
    all_users = await user_repo.get_all(filters={"role": UserRole.USER})
    assert len(all_users) == 2

    # 4. Pagination
    paginated = await user_repo.get_all(filters={"role": UserRole.USER}, page=1, page_size=1)
    assert len(paginated) == 1

    # 5. Sorting
    sorted_asc = await user_repo.get_all(filters={"role": UserRole.USER}, sort_by=["email"])
    assert sorted_asc[0].email == "rep_u1@example.com"

    sorted_desc = await user_repo.get_all(filters={"role": UserRole.USER}, sort_by=["-email"])
    assert sorted_desc[0].email == "rep_u2@example.com"

    # 6. Exists & Count
    assert await user_repo.exists(email="rep_u1@example.com") is True
    assert await user_repo.exists(email="non_existent@example.com") is False
    assert await user_repo.count(role=UserRole.USER) == 2

    # 7. Soft Delete
    deleted = await user_repo.delete(u1.id)
    assert deleted is True
    assert u1.is_deleted is True  # Soft deleted

    # 8. Hard Delete
    hard_deleted = await user_repo.hard_delete(u2.id)
    assert hard_deleted is True
    fetched_u2 = await user_repo.get_by_id(u2.id)
    assert fetched_u2 is None


@pytest.mark.asyncio
async def test_custom_user_repository(db_session: AsyncSession) -> None:
    """Verify UserRepository specific methods."""
    user_repo = UserRepository(db_session)
    user = User(email="auth_user@example.com", is_active=True)
    await user_repo.create(user)

    # get_by_email
    db_user = await user_repo.get_by_email("auth_user@example.com")
    assert db_user is not None
    assert db_user.id == user.id

    # deactivate
    await user_repo.deactivate(user.id)
    assert user.is_active is False

    # activate
    await user_repo.activate(user.id)
    assert user.is_active is True


@pytest.mark.asyncio
async def test_custom_product_repository(db_session: AsyncSession) -> None:
    """Verify ProductRepository search and filters."""
    cat_repo = CategoryRepository(db_session)
    prod_repo = ProductRepository(db_session)

    category = Category(name="Mobiles", slug="mobiles")
    await cat_repo.create(category)

    p1 = Product(
        title="Apple iPhone 15 Pro",
        brand="Apple",
        model_name="iPhone 15",
        status=ProductStatus.ACTIVE,
        category_id=category.id,
    )
    p2 = Product(
        title="Samsung Galaxy S24",
        brand="Samsung",
        model_name="S24 Ultra",
        status=ProductStatus.ACTIVE,
        category_id=category.id,
    )
    await prod_repo.create_many([p1, p2])

    # Search Title / Brand
    results = await prod_repo.search_products("iPhone")
    assert len(results) == 1
    assert results[0].brand == "Apple"

    # Search Category
    results_cat = await prod_repo.get_by_category(category.id)
    assert len(results_cat) == 2

    # Search Brand
    results_brand = await prod_repo.get_by_brand("Samsung")
    assert len(results_brand) == 1


@pytest.mark.asyncio
async def test_custom_wishlist_repository(db_session: AsyncSession) -> None:
    """Verify WishlistRepository adding/removing items."""
    user_repo = UserRepository(db_session)
    prod_repo = ProductRepository(db_session)
    wish_repo = WishlistRepository(db_session)
    item_repo = WishlistItemRepository(db_session)

    user = User(email="shopper@example.com")
    product = Product(title="Cool Gadget", status=ProductStatus.ACTIVE)
    await user_repo.create(user)
    await prod_repo.create(product)

    wishlist = Wishlist(user_id=user.id, name="Favorites")
    await wish_repo.create(wishlist)

    # add_product
    item = await wish_repo.add_product(wishlist.id, product.id, desired_price=Decimal("99.99"))
    assert item.id is not None

    # Verify added
    items = await item_repo.get_all(filters={"wishlist_id": wishlist.id})
    assert len(items) == 1
    assert items[0].product_id == product.id

    # remove_product
    removed = await wish_repo.remove_product(wishlist.id, product.id)
    assert removed is True

    items_after = await item_repo.get_all(filters={"wishlist_id": wishlist.id})
    assert len(items_after) == 0


@pytest.mark.asyncio
async def test_custom_notification_repository(db_session: AsyncSession) -> None:
    """Verify NotificationRepository unread counters and bulk read marks."""
    user_repo = UserRepository(db_session)
    notif_repo = NotificationRepository(db_session)

    user = User(email="notified@example.com")
    await user_repo.create(user)

    n1 = Notification(
        user_id=user.id,
        title="Alert 1",
        message="Alert msg 1",
        type=NotificationType.PRICE_DROP,
        is_read=False,
    )
    n2 = Notification(
        user_id=user.id,
        title="Alert 2",
        message="Alert msg 2",
        type=NotificationType.SYSTEM,
        is_read=False,
    )
    await notif_repo.create_many([n1, n2])

    # Unread count
    assert await notif_repo.get_unread_count(user.id) == 2

    # Mark all as read
    updated = await notif_repo.mark_all_as_read(user.id)
    assert updated == 2
    assert await notif_repo.get_unread_count(user.id) == 0


@pytest.mark.asyncio
async def test_custom_price_history_and_reviews(db_session: AsyncSession) -> None:
    """Verify PriceHistory trends and ProductReview SQL aggregations."""
    prod_repo = ProductRepository(db_session)
    merch_repo = MerchantRepository(db_session)
    offer_repo = ProductPriceRepository(db_session)
    hist_repo = PriceHistoryRepository(db_session)
    rev_repo = ProductReviewRepository(db_session)

    product = Product(title="Compare Model X", status=ProductStatus.ACTIVE)
    merchant = Merchant(name="ShopY", domain="shopy.com")
    await prod_repo.create(product)
    await merch_repo.create(merchant)

    offer = ProductPrice(
        product_id=product.id,
        merchant_id=merchant.id,
        price=Decimal("150.00"),
        url="https://shopy.com/x",
        last_updated=datetime.now(UTC),
    )
    await offer_repo.create(offer)

    # 1. Price History
    h1 = PriceHistory(product_price_id=offer.id, price=Decimal("160.00"), recorded_at=datetime(2026, 1, 1, tzinfo=UTC))
    h2 = PriceHistory(product_price_id=offer.id, price=Decimal("150.00"), recorded_at=datetime(2026, 1, 2, tzinfo=UTC))
    await hist_repo.create_many([h1, h2])

    trends = await hist_repo.get_price_trends(offer.id)
    assert len(trends) == 2
    assert trends[0].price == Decimal("160.00")  # Sorted ascending by date

    min_max = await hist_repo.get_min_max_prices(offer.id)
    assert min_max == (Decimal("150.00"), Decimal("160.00"))

    # 2. Reviews
    r1 = ProductReview(product_id=product.id, rating=5.0, source=ReviewSource.INTERNAL)
    r2 = ProductReview(product_id=product.id, rating=3.0, source=ReviewSource.INTERNAL)
    await rev_repo.create_many([r1, r2])

    avg_rating = await rev_repo.get_average_rating(product.id)
    assert avg_rating == 4.0


@pytest.mark.asyncio
async def test_error_handling_and_rollback(db_session: AsyncSession) -> None:
    """Verify that database constraint violations cause transaction rollbacks and raise RepositoryError."""
    user_repo = UserRepository(db_session)

    u1 = User(email="unique_email@example.com")
    await user_repo.create(u1)
    await db_session.commit()

    # Try creating user with duplicate email
    u2 = User(email="unique_email@example.com")
    with pytest.raises(RepositoryError):
        await user_repo.create(u2)
