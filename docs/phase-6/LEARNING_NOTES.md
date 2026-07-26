# Educational Mentorship Notes: Phase 6
## AI Shopping Assistant Backend

This document contains deep-dive educational notes explaining how SQLAlchemy ORM, Alembic, and PostgreSQL function internally.

---

## 1. How SQLAlchemy 2.0 Works Internally

### 1.1 Declarative Mapping & MetaData
When Python loads the models, SQLAlchemy parses class definitions inheriting from `BaseModel`.
* **`DeclarativeBase`**: Acts as a metaclass registry.
* **`Base.metadata`**: A collection of `Table` schema descriptions. Every class definition containing `Mapped[...]` columns registers a matching `Table` object inside this metadata registry.
* **`Mapped[T]`**: Generates static type-checking annotations. MyPy/Pyright read `Mapped[str]` to know that the python property is a string, while SQLAlchemy compiles it to the appropriate column mapping.
* **`mapped_column()`**: The core column builder. It configures physical database settings like nullable, unique, indexes, or custom SQL check constraints.

### 1.2 Python-to-SQL Compilation
When you execute a query using an async session:
```python
query = select(Product).where(Product.brand == "Dell")
result = await session.execute(query)
```
1. **Compilation**: SQLAlchemy looks up the dialect (in our case, `asyncpg` for PostgreSQL). It translates the abstract AST (Abstract Syntax Tree) query object into raw SQL text:
   `SELECT products.id, products.title, ... FROM products WHERE products.brand = $1`
2. **Parameters Bind**: The value `"Dell"` is safely bound to placeholder `$1` using prepared statements, preventing SQL injection.
3. **Execution**: The query is sent as binary protocol packets over a TCP socket via `asyncpg` to the database.

---

## 2. How PostgreSQL Stores Data Internally

* **Pages & Rows**: PostgreSQL stores table records inside 8KB memory blocks called **Pages**. Each page contains a header, line pointers, and physical row data (tuples).
* **MVCC (Multi-Version Concurrency Control)**: PostgreSQL handles concurrent transactions without locking tables by preserving old row versions on update/delete. 
  - An `UPDATE` operation writes a *new* row copy containing the updated values and marks the *old* row version as expired.
  - A `DELETE` operation simply marks the row version as expired.
  - Expired rows ("dead tuples") are removed by the background `vacuum` worker, returning page space back to the operating system.
* **B-Tree Index Traverse**: B-Tree indexes store key values in a sorted tree structure. When searching by primary key (UUID), PostgreSQL traverses down the tree leaves to locate the page offset containing the target row version, avoiding full-table scans.

---

## 3. How Sessions Manage Transactions

The session factory configuration in `src/infrastructure/db/session.py` uses `async_sessionmaker`:
* **`expire_on_commit=False`**: Prevents the session from clearing object attributes after a commit transaction. In async programming, this is vital because accessing expired properties outside a transaction triggers lazy SELECT statements that block the event loop.
* **`autoflush=False`**: Prevents the session from flushing changes to the database automatically before a query execution, giving the developer complete control over transactional boundaries.

### Common Junior Developer Pitfalls:
1. **Missing await on Session calls**:
   * *Mistake*: `session.commit()`
   * *Correct*: `await session.commit()`
   * *Result of mistake*: The transaction remains uncommitted in a pending state, causing locks and leaks.
2. **Accessing lazy-loaded relations outside session context**:
   * *Mistake*: Returning database models from a service layer to API routes and letting FastAPI serialize them. If relationships (like `product.prices`) are lazy-loaded, Pydantic tries to read them, raising an `MissingGreenletContext` error because the database session has already closed.
   * *Correct*: Use `selectinload` or `joinedload` inside the repository to pre-fetch relationships before closing the session.
