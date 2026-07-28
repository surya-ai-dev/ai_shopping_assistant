# Phase 7 Developer Workflow: Repository Layer
## AI Shopping Assistant Backend

---

## 1. Overview

This document describes the standard developer workflow for modifying, creating, and testing database repositories in the **AI Shopping Assistant Backend**. Following this workflow ensures that database logic remains isolated from business logic, types remain safe, and integration tests run cleanly.

---

## 2. Repository Creation Workflow

When introducing new entities to the system, follow this developer lifecycle:

```
+--------------------------+
|  Create SQLAlchemy Model |  <-- Define in src/models/
+--------------------------+
             |
             v
+--------------------------+
|  Generate DDL Migration  |  <-- Run 'alembic revision --autogenerate'
+--------------------------+
             |
             v
+--------------------------+
|    Create Repository     |  <-- Inherit BaseRepository in src/repositories/
+--------------------------+
             |
             v
+--------------------------+
|   Register Repository    |  <-- Add to __init__.py export mapping
+--------------------------+
             |
             v
+--------------------------+
|    Write Integration     |  <-- Add test cases under tests/integration/
+--------------------------+
             |
             v
+--------------------------+
|   Verify CRUD passes     |  <-- Run pytest
+--------------------------+
```

---

## 3. CRUD Lifecycle

A typical data operations request traverses the application layers as follows:

```
Client         FastAPI API Route      Service Layer      Repository Layer      SQLAlchemy      PostgreSQL
  |                    |                    |                   |                   |               |
  |--- HTTP POST ----->|                    |                   |                   |               |
  |                    |--- call service -->|                   |                   |               |
  |                    |                    |--- create(model)->|                   |               |
  |                    |                    |                   |--- add() -------->|               |
  |                    |                    |                   |--- flush() ------>|               |
  |                    |                    |                   |                   |--- INSERT --->|
  |                    |                    |                   |                   |<-- PK id -----|
  |                    |                    |<-- return entity -|-------------------|               |
  |                    |                    |--- commit() ----->|                   |               |
  |                    |                    |                   |--- commit() ----->|               |
  |                    |                    |                   |                   |--- COMMIT --->|
  |                    |<-- return result --|                   |                   |               |
  |<-- JSON Response --|                    |                   |                   |               |
```

---

## 4. Creating New Repositories (Step-by-Step)

To create a repository for a new entity (e.g. `Coupon`):

### Step 1: Declare the ORM Model
Create `src/models/coupon.py` inheriting from `BaseModel`, `UUIDMixin`, and `TimestampMixin`:
```python
from sqlalchemy import String, Numeric
from sqlalchemy.orm import interfaces, Mapped, mapped_column
from src.models.base import BaseModel
from src.models.mixins import UUIDMixin, TimestampMixin

class Coupon(BaseModel, UUIDMixin, TimestampMixin):
    __tablename__ = "coupons"
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
```

### Step 2: Implement the Repository
Create `src/repositories/coupon.py` inheriting from `BaseRepository`:
```python
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.coupon import Coupon
from src.repositories.base import BaseRepository

class CouponRepository(BaseRepository[Coupon]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Coupon)
```

### Step 3: Register in `src/repositories/__init__.py`
```python
from src.repositories.coupon import CouponRepository

__all__ = [
    ...,
    "CouponRepository",
]
```

---

## 5. Adding Custom Repository Methods

Custom queries belong in the specific entity's repository class, utilizing database indexes and eager loading options:

### Example A: Unique Field Fetching (`get_by_email`)
```python
class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> User | None:
        return await self.get_by_field("email", email)
```

### Example B: Hierarchical Querying (`get_subcategory_tree`)
Avoid nested database queries inside loops. Use eager loader options `selectinload` to fetch hierarchies in one query:
```python
from sqlalchemy.orm import interfaces, selectinload
from sqlalchemy import select

class CategoryRepository(BaseRepository[Category]):
    async def get_subcategory_tree(self, parent_id: UUID) -> Category | None:
        stmt = (
            select(Category)
            .options(selectinload(Category.children))
            .where(Category.id == parent_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

### Example C: Fuzzy Keyword Search (`search_products`)
```python
from sqlalchemy import or_, select

class ProductRepository(BaseRepository[Product]):
    async def search_products(self, query: str) -> Sequence[Product]:
        stmt = select(Product).where(
            or_(
                Product.title.ilike(f"%{query}%"),
                Product.brand.ilike(f"%{query}%")
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

---

## 6. Transaction Workflow

Manage transactions sequentially using repository boundary controls:

```
   Start Workflow
         |
         v
+------------------+
|  Begin Session   |  <-- Handled by FastAPI Depends(get_async_session)
+------------------+
         |
         v
+------------------+
|  Perform CRUD    |  <-- Call repo.create(), repo.update(), etc.
+------------------+
         |
         v
+------------------+
|   Flush Session  |  <-- Call repo.flush() to validate DB constraints
+------------------+
         |
         +-----------------------+
         | (Success)             | (Failure / Exception)
         v                       v
+------------------+     +------------------+
|  Commit Session  |     | Rollback Session |
+------------------+     +------------------+
         |                       |
         v                       v
    End Session             End Session
```

---

## 7. Query Workflow (Filtering, Sorting, Pagination)

Always expose sorting, filtering, and pagination properties at the generic query layer:

```python
results = await product_repo.get_all(
    filters={"brand": "Apple", "status": ProductStatus.ACTIVE},  # Ignores None variables
    sort_by=["-created_at", "title"],                            # Prefix '-' for DESC
    page=1,                                                       # 1-based page
    page_size=20                                                  # Page size limit
)
```

---

## 8. Async Workflow & Session Lifecycle

SQLAlchemy's `AsyncSession` is designed to be **non-thread-safe and scoped to a single request lifecycle**:

1. **FastAPI Injection**: Inject the session dependency into endpoints:
   ```python
   @app.post("/products")
   async def add_product(payload: ProductCreate, session: AsyncSession = Depends(get_async_session)):
       repo = ProductRepository(session)
       # ...
   ```
2. **Dispose Connections**: FastAPI's context manager automatically yields the session, commits on route completion, and rolls back if an exception occurs.
3. **Connection Pooling**: `asyncpg` manages the database socket pool under the hood. Avoid instantiating new `AsyncEngine` configurations within function lifecycles.

---

## 9. Repository Testing Workflow

Always verify repository changes using integration tests with isolated database transactions:

1. **Scope Test Fixtures**: Declare database connections and engines as **function-scoped** to ensure clean states:
   ```python
   @pytest.fixture
   async def test_engine():
       engine = create_async_engine(db_url)
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       yield engine
       async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.drop_all)
       await engine.dispose()
   ```
2. **Auto-Rollback**: Wrap each test execution block in `await session.rollback()` to prevent test data leaks.
3. **No Mocks on DB Tests**: Run integration tests against a live PostgreSQL container to test real index traversals, unique constraints, and check constraints.

---

## 10. Alembic Workflow

To update your database schema:

```
[ Modify Python model class in src/models/ ]
                     |
                     v
[ Run 'alembic revision --autogenerate -m "description"' ]
                     |
                     v
[ Inspect the generated file under alembic/versions/ ]
                     |
                     v
[ Run 'alembic upgrade head' to apply changes ]
                     |
                     v
[ Run 'pytest tests/integration/' to verify constraints ]
```

---

## 11. Debugging Guide

### 1. `asyncpg.exceptions.InterfaceError: another operation is in progress`
* **Cause**: Attempting to run a database query while another operation is still awaiting execution on the same connection. Often caused by sharing a module-scoped engine across different event loops in tests.
* **Fix**: Ensure that all pytest database fixtures are function-scoped (not module-scoped) and that you `await` every repository method call.

### 2. `IntegrityError` (Unique Constraint / Foreign Key Violations)
* **Cause**: Trying to insert a duplicate value in a unique column (e.g. duplicate email) or referencing a non-existent parent ID.
* **Fix**: Wrap repository modifications in try-except blocks, log the details, call `await session.rollback()`, and translate the error into a `RepositoryError`.

### 3. `InvalidRequestError` (Table already defined)
* **Cause**: Multiple classes mapped to the same table name are imported into the same SQLAlchemy metadata instance.
* **Fix**: Ensure that legacy model packages (such as `src.infrastructure.db.models`) are not imported into the metadata registry in Phase 6/7 tests.

---

## 12. Repository Best Practices

1. **Expose No ORM Constructs**: Never return raw SQLAlchemy query structures or select statements to the Service Layer. Always return domain model entities.
2. **Never Commit inside Repository Queries**: Do not call `self.session.commit()` inside search, create, or update operations unless writing explicit transactional utility methods. Let the caller decide transaction boundaries.
3. **Always Log Execution Times**: Log timing metrics for slow database queries (e.g. search, tree loads) using `time.perf_counter()`.
4. **Use Explicit Eager Loading**: Prevent N+1 queries by configuring `selectinload` or `joinedload` on all relationship lookups.

---

## 13. Production Checklist

Before merging repository modifications, verify:

- [ ] **Type Annotations**: All method signatures are fully annotated. Generic types are bound to `BaseModel`.
- [ ] **Eager Loading**: Relations are loaded explicitly to prevent N+1 queries.
- [ ] **Indexing**: Query filter columns are covered by btree, GIN, or trigram indexes.
- [ ] **Rollback Coverage**: All write statements roll back the session on failure.
- [ ] **Mypy Compliant**: Running `mypy src` passes with no issues.
- [ ] **Ruff Checked**: Running `ruff check .` reports zero violations.
- [ ] **Tests Pass**: Integration tests pass successfully.

---

## 14. Summary

To save data into PostgreSQL:
1. The client sends an HTTP POST request.
2. FastAPI yields an `AsyncSession` from the session factory.
3. The Service Layer initializes a repository and passes the session.
4. The Service invokes `repository.create(entity)`.
5. The repository translates the payload, adds it to the session, and executes a database flush.
6. The database generates a UUID and validates constraints.
7. The Service Layer commits the transaction, and the database writes the record to disk.
