# Phase 7 Architecture: Repository Layer
## AI Shopping Assistant Backend

---

## 1. High-Level Purpose

In enterprise application development, coupling database driver logic with core business rules is a primary source of technical debt. When service layers execute raw database queries, they become tightly bound to a specific database technology, ORM, and schema structure.

The **Repository Layer** exists as a decoupling mechanism that abstracts data persistence. It acts as an in-memory collection of domain entities, shielding the business core (the Application Layer) from database-specific details.

```
+---------------------------------------------------------+
|                  APPLICATION/SERVICE LAYER              |
|   (Enforces business invariants, coordinates use cases)  |
+---------------------------------------------------------+
                             |
                      [Interface/Type]
                             v
+---------------------------------------------------------+
|                    REPOSITORY LAYER                     |
|  (Abstracts queries, handles transactions & rollbacks)  |
+---------------------------------------------------------+
                             |
                      [ORM Statements]
                             v
+---------------------------------------------------------+
|                 PERSISTENCE LAYER (SQLAlchemy)          |
|  (Manages connection pools, compiles SQL statements)   |
+---------------------------------------------------------+
                             |
                       [Wire protocol]
                             v
+---------------------------------------------------------+
|                    POSTGRESQL DATABASE                  |
|          (Performs disk writes, traverses indexes)      |
+---------------------------------------------------------+
```

### Problems Solved by the Repository Layer:
1. **Business Logic Pollution**: Prevents SQL compilation and database-driver logic (such as session commits or database exceptions) from leaking into business operations.
2. **Testing Impedance**: When database logic is embedded in services, unit testing requires setting up database connections. By isolating data access in repositories, services can be easily tested using mock repositories.
3. **ORM Lock-in**: Decouples the application from SQLAlchemy. If the system needs to swap SQLAlchemy for raw SQL, a document store, or an external API, only the repository implementation changes; the business layer remains untouched.

---

## 2. Clean Architecture Position

Clean Architecture organizes code into concentric layers with a strict dependency rule: **inner layers cannot know anything about outer layers**.

```
       +---------------------------------------------+
       |               PRESENTATION LAYER            |
       |             (FastAPI / REST APIs)           |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |               APPLICATION LAYER             |
       |          (Business Use Cases / Services)    |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |               REPOSITORY LAYER              |
       |         (Data Access Interfaces / Concrete)  |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |              PERSISTENCE LAYER              |
       |            (SQLAlchemy / asyncpg)           |
       +---------------------------------------------+
                              |
                              v
       +---------------------------------------------+
       |                 DATABASE LAYER              |
       |                  (PostgreSQL)               |
       +---------------------------------------------+
```

* **Presentation Layer**: Exposes endpoints and handles HTTP serialization/deserialization.
* **Application Layer**: Houses business workflows. It invokes repositories to fetch, update, or write entities.
* **Repository Layer**: Implements translation logic, turning business-level queries into SQL execution blocks.
* **Persistence Layer**: Implements the technical database driver and session pooling.
* **Database Layer**: Persists records on disk.

---

## 3. Repository Pattern & Dependency Inversion

The Repository Layer uses the **Dependency Inversion Principle (DIP)**:
1. The **Application Layer** defines an *interface* (or contract) describing how data should be retrieved (e.g. `get_by_id`).
2. The **Repository Layer** provides a *concrete implementation* of this interface using SQLAlchemy.
3. The **Service Layer** depends on the abstract interface, not the concrete implementation.

### Why Services Should Never Use SQLAlchemy Directly:
* **Connection Leakage**: If services manage sessions directly, an unhandled exception in business logic can leave connection pools exhausted or transactions open.
* **Complex Schema Adjustments**: Changing a table column name would require refactoring every service file that queries it. With repositories, schema changes are localized to a single file.
* **Readability**: Services should read like a sequence of business tasks (e.g. `user = repo.get_by_email(email)`), not database operations (e.g. `session.execute(select(User).where(User.email == email))`).

---

## 4. Generic Repository Design

Most database models share standard CRUD requirements. The `BaseRepository[ModelType]` uses Python generics to consolidate these queries into a single, reusable class.

```python
ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self.session = session
        self.model = model
```

* **ModelType**: Constrained to subclasses of `BaseModel`.
* **Reductions in Duplicate Code**: By inheriting from `BaseRepository`, custom repositories automatically inherit fully typed implementations of `create`, `get_by_id`, `get_all`, `update`, `delete`, `count`, and `exists` without writing a single line of database driver code.

---

## 5. Concrete Repositories

Each of our 12 tables has a corresponding concrete repository subclassing `BaseRepository`. They hold queries specific to their business logic:

1. **UserRepository**: Handles user authentication, email lookups (`get_by_email`), and account activation/deactivation.
2. **ProductRepository**: Houses fuzzy keyword searches on product catalogs (`search_products`), brand filters, and category-level queries.
3. **MerchantRepository**: Queries active stores matching specific domains (`get_by_domain`) or verification status.
4. **CategoryRepository**: Resolves parent-child hierarchies, fetching root taxonomy nodes and child trees.
5. **WishlistRepository**: Handles adding and removing product listings to a user's wishlist.
6. **WishlistItemRepository**: Isolates wishlist intersection links, returning alert thresholds for price drop workers.
7. **ProductPriceRepository**: Aggregates price offers, sorting listings from cheapest to most expensive (`get_active_offers`).
8. **PriceHistoryRepository**: Pulls historical price records chronologically for charting trends.
9. **NotificationRepository**: Counts unread notification badges (`get_unread_count`) and marks user alerts as read.
10. **SearchHistoryRepository**: Logs queries and extracts trending query terms via SQL counting.
11. **ProductReviewRepository**: Calculates rating averages and lists reviews filtered by rating score or source.
12. **ProductImageRepository**: Retrieves sorted product images and handles gallery reordering.

---

## 6. CRUD Flow

Here is how data flows through the Repository Layer:

### 1. Create Operation
```
Service Layer           Repository (Base)          AsyncSession           PostgreSQL
      |                         |                        |                     |
      |--- create(entity) ----->|                        |                     |
      |                         |--- session.add(ent) -->|                     |
      |                         |--- session.flush() ---->|                     |
      |                         |<-- (autogenerated id)--|                     |
      |<-- return entity -------|                        |                     |
```

### 2. Read Operation
```
Service Layer           Repository (Base)          AsyncSession           PostgreSQL
      |                         |                        |                     |
      |--- get_by_id(id) ------>|                        |                     |
      |                         |--- session.execute() ->|                     |
      |                         |                        |--- SELECT * --------|
      |                         |                        |<-- database rows ---|
      |                         |<-- ORM entity ---------|                     |
      |<-- return entity -------|                        |                     |
```

### 3. Update Operation
```
Service Layer           Repository (Base)          AsyncSession           PostgreSQL
      |                         |                        |                     |
      |--- update(id, data) --->|                        |                     |
      |                         |--- get_by_id(id) ----->|                     |
      |                         |<-- entity -------------|                     |
      |                         |                        |                     |
      |                         |--- (apply changes) --->|                     |
      |                         |--- session.flush() ---->|                     |
      |                         |                        |--- UPDATE statement-|
      |                         |                        |<-- flush success ---|
      |<-- return entity -------|                        |                     |
```

### 4. Delete Operation (Soft Delete)
```
Service Layer           Repository (Base)          AsyncSession           PostgreSQL
      |                         |                        |                     |
      |--- delete(id) --------->|                        |                     |
      |                         |--- get_by_id(id) ----->|                     |
      |                         |<-- entity -------------|                     |
      |                         |                        |                     |
      |                         |--- soft_delete() ----->|                     |
      |                         |    (is_deleted=True)   |                     |
      |                         |--- session.flush() ---->|                     |
      |                         |                        |--- UPDATE statement-|
      |<-- return True ---------|                        |                     |
```

---

## 7. Query Features

* **Filtering**: Filters columns dynamically via dictionary mapping. Null query arguments (e.g. `brand=None`) are automatically skipped:
  ```python
  clean_filters = {k: v for k, v in filters.items() if v is not None}
  ```
* **Sorting**: Decodes string sorting lists (e.g. `sort_by=["-price", "created_at"]`), automatically calling `desc()` on column variables if prefixed with a minus.
* **Pagination**: Utilizes standard 1-based page variables to calculate SQL page offsets: `offset = (page - 1) * page_size`, which is calculated on the database side to prevent loading large tables in memory.
* **Searching**: `ProductRepository.search_products()` executes fuzzy ILIKE queries on titles, brands, and model names.
* **Count / Exists**:
  - `count()` compiles SQL `func.count()` to return fast counts of matched rows.
  - `exists()` runs a lightweight query selecting only the primary key column to check for record existence.
* **Bulk Operations**: `create_many()` executes `session.add_all()` to write multiple rows in a single batch, reducing round-trip latency.

---

## 8. Transaction Management

Transaction boundaries are managed via the SQLAlchemy `AsyncSession` API:
* **commit()**: Commits the current transaction, writing all changes permanently to disk.
* **rollback()**: Rolls back the current transaction, discarding all uncommitted changes.
* **flush()**: Sends pending modifications to the database. The database registers the changes but does not commit them. This generates primary keys and validates constraints without finalizing the transaction.
* **refresh()**: Reloads an object's attributes from the database, ensuring the in-memory entity matches the database state.

### Transaction Boundaries:
In Clean Architecture, **Service workflows define the transaction boundaries**. This allows a service to orchestrate multiple repository writes and commit them atomically. If any operation fails, calling `rollback()` reverts all changes made in that request.

---

## 9. Error Handling & Translation

To decouple the application from database-specific libraries, we use **Exception Translation**:

```
[ PostgreSQL Driver (asyncpg) ]
             | (Raises IntegrityError/SocketError)
             v
[   SQLAlchemy ORM Mapper    ]
             | (Raises SQLAlchemyError)
             v
[      Repository Layer      ] <--- Catch, rollback session, raise RepositoryError
             | (Raises RepositoryError)
             v
[   Application / Service    ] <--- Clean, technology-agnostic exception handling
```

By translation, the Service Layer does not need to import `sqlalchemy.exc.IntegrityError`. It simply catches `RepositoryError`, ensuring the business layer remains independent of the database driver.

---

## 10. Dependency Graph

The import direction is strictly unidirectional:

```
    src/repositories/ (Concrete Repository Implementation)
           |
           v
    src/models/       (SQLAlchemy Declarative Entities)
           |
           v
    SQLAlchemy        (ORM Engine Mapper)
           |
           v
    PostgreSQL        (Relational Database Store)
```

### Why Circular Imports Must Be Avoided:
In Python, circular imports (e.g., Module A imports Module B, and Module B imports Module A) cause runtime initialization failures. We prevent this in our repository design by:
1. Keeping models decoupled from repositories.
2. Defining all generic classes in `base.py` and inheriting from them sequentially.
3. Importing relationship entities inside models only within `if TYPE_CHECKING:` blocks.

---

## 11. SOLID Principles in Repositories

* **Single Responsibility Principle (SRP)**: Each repository has a single responsibility: data access for its corresponding model. It does not handle business logic (like verifying user permissions).
* **Open-Closed Principle (OCP)**: `BaseRepository` provides generic CRUD operations. If we introduce a new database model, we extend the system by writing a new repository subclass, without modifying the existing generic base code.
* **Liskov Substitution Principle (LSP)**: All custom repositories inherit from `BaseRepository`. They can be substituted for `BaseRepository` instances of their target model without breaking the query pipelines.
* **Interface Segregation Principle (ISP)**: Custom repositories expose only the query methods relevant to their entity, keeping interfaces focused and decoupled.
* **Dependency Inversion Principle (DIP)**: Services depend on repository abstractions rather than concrete database connections, allowing data access mechanisms to be swapped out easily.

---

## 12. Clean Architecture Rules

### Repositories MAY Import:
* Declarative ORM models (`src/models/*`).
* SQLAlchemy query utilities (`select`, `update`, `delete`, `joinedload`, `selectinload`).
* Project exceptions (`RepositoryError`).
* Standard library typing tools and domain-specific enums.

### Repositories must NEVER Import:
* Presentation-layer structures (FastAPI classes, REST controllers).
* Service classes (which would introduce circular dependencies).
* HTTP parser models or presentation mappers.

---

## 13. Performance Considerations

* **Database Indexes**: Queries use database indexes to speed up lookups:
  - btree indexes cover foreign keys (`product_id`, `category_id`, `merchant_id`).
  - GIN indexes cover product specification fields (`attributes`) for fast JSON queries.
  - Trigram indexes speed up fuzzy keyword searches on product titles.
* **Pagination**: Prevents database and application memory exhaustion by returning data in paginated chunks instead of fetching entire tables.
* **Eager vs. Lazy Loading (N+1 Prevention)**:
  - *Lazy Loading*: Fetches related entities only when accessed, triggering an additional SQL query for each relation. In loops, this causes the **N+1 query problem** (1 query to fetch products, and N queries to fetch the category for each product).
  - *Eager Loading*: Solves this by fetching related entities in the initial query using `joinedload` (for Many-to-One relations) or `selectinload` (for One-to-Many relations), reducing N+1 queries to a single query.
* **Batch Inserts**: `create_many()` uses SQLAlchemy's batching capabilities to insert multiple records in a single database round-trip, optimizing bulk data operations.

---

## 14. Async Architecture

Our repository layer is built on SQLAlchemy's asynchronous API:
* **AsyncSession**: Performs non-blocking database queries. While waiting for PostgreSQL to return rows, the event loop can process other incoming API requests, improving application throughput.
* **Connection Pooling**: Reuses a pool of open database connections, avoiding the overhead of establishing a new connection for every query.
* **Await**: Every query execution and transactional state change is awaited, ensuring that execution yields control back to the event loop during database I/O.

---

## 15. Production Readiness

* **Scalability**: Paginated queries, database aggregations, and trigram indexing ensure fast response times as the database grows.
* **Maintainability**: Clear division of responsibilities makes it easy to add, modify, or debug query operations.
* **Extensibility**: Swapping database technologies or adding features (like caching) can be done inside the repository layer without modifying business workflows.
* **Testing**: Database engines and connection pools are scoped to test functions, ensuring clean database schemas and complete test isolation.
* **Thread Safety**: SQLAlchemy's `AsyncSession` is not thread-safe. By utilizing function-scoped sessions in FastAPI requests and integration tests, we ensure that sessions are never shared across concurrent execution paths.

---

## 16. Summary

The Repository Layer provides a clean, decoupled data access layer for the AI Shopping Assistant backend. By using **Python Generics**, the `BaseRepository` provides standard CRUD operations for all database models, reducing boilerplate code. Custom repositories extend this base class to implement index-friendly domain queries. 

Through **Dependency Inversion**, database logic is kept separate from business logic, ensuring the application remains maintainable, testable, and highly performant.
