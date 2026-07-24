# Phase 5 – Persistent Storage Layer

This guide explains the architecture, design, and implementation of the persistent PostgreSQL storage layer introduced in Phase 5 of the AI Shopping Assistant project.

---

## 1. Architecture

Phase 5 transitions the system from transient in-memory storage to a production-grade PostgreSQL persistence layer. We preserve Clean Architecture by strictly separating domain logic from database configurations, using the Repository Pattern and Mapper Layer.

### System Diagram

```
User / Scraping Pipeline
           │
           ▼
┌──────────────────────────────────────┐
│  ProductRepositoryInterface (Domain)  │
└──────────────────┬───────────────────┘
                   │  Implements
                   ▼
┌──────────────────────────────────────┐
│  PostgresProductRepository           │
│  (Infrastructure Layer)              │
└──────────────────┬───────────────────┘
                   │  Uses
                   ▼
┌──────────────────────────────────────┐
│  Mapper (domain_to_orm / orm_to_domain)│
└──────────────────┬───────────────────┘
                   │  Maps to
                   ▼
┌──────────────────────────────────────┐
│  ProductORM / Database Entities      │
└──────────────────────────────────────┘
```

---

## 2. Folder Structure

The newly created and populated folders under `src/` are:

```
src/
├── database/            # Database engine and connection pool management
│   ├── __init__.py      # Exports session context and initialization helpers
│   ├── base.py          # SQLAlchemy 2.0 Base class and TimestampMixin
│   ├── config.py        # DatabaseConfig extracting URLs from settings
│   ├── connection.py    # Singleton AsyncEngine instantiation & cleanup
│   └── session.py       # Asynchronous session factory and transactional context
├── orm/                 # SQLAlchemy 2.0 ORM models (strictly separated from Domain)
│   ├── __init__.py      # Package level model exports
│   └── models.py        # ProductORM, PriceHistoryORM, ImageORM, SpecificationORM
├── mappers/             # Convert between ORM entities and Clean Domain models
│   ├── __init__.py      # Package level mapper exports
│   └── product.py       # domain_to_orm and orm_to_domain mapping functions
└── repositories/        # Repository implementations
    └── postgres/
        ├── __init__.py  # Exports PostgresProductRepository
        └── product.py   # PostgresProductRepository implementation of interface
```

---

## 3. Database Design

We map the core domain model structure to PostgreSQL tables using normalized relational schemas:

* **products**: Master table representing the product listing. Includes indexed fields for fast lookup: `site_id`, `url`, `sku`, `brand`, `model_name`, `category`.
* **product_specs**: Technical specs mapping to product entries via a foreign key on `products.id` with a unique constraint (one-to-one relationship).
* **price_history**: Audit logs representing historical price variations over time (one-to-many relationship).
* **product_images**: Stores image URLs linked to a product ID (one-to-many relationship).
* **product_fingerprints**: Cross-site deduplication hashes containing unique `hash_key` lookups.

---

## 4. Runtime Flow

1. The scraper pipeline finishes scraping, parsing, and validating a product.
2. The pipeline calls `ProductRepositoryInterface.save(product)`.
3. Under PostgreSQL mode, `PostgresProductRepository` intercepts the call, maps the domain `Product` entity into database-compatible ORM models using the Mapper Layer.
4. `PostgresProductRepository` checks if the product canonical URL (or fingerprint) already exists in the database.
5. If found, it issues an `UPDATE` on mutable fields and appends a new `PriceHistoryORM` log.
6. If not found, it performs an `INSERT` of the main product entity along with specification, fingerprint, image, and initial price history relations.
7. Database state modifications are committed atomically at the end of the transaction scope.

---

## 5. Repository Pattern

By using the `ProductRepositoryInterface`, the domain layer remains unaware of where products are stored. This makes it trivial to swap storage backends (e.g., swapping `InMemoryProductRepository` with `PostgresProductRepository`) by updating the dependency injection configuration.

---

## 6. Mapper Layer

To prevent database annotations (such as SQLAlchemy imports or primary/foreign key mappings) from leaking into the domain, the Mapper Layer acts as a bi-directional translation interface:
* `domain_to_orm(product: Product) -> ProductORM`: Serializes clean domain entities into database ORM classes.
* `orm_to_domain(orm: ProductORM) -> Product`: Deserializes database rows into rich, validated domain models.

---

## 7. Transaction Flow

All database state modifications conform to ACID properties:
* **Connection Context**: Async database sessions are managed via `get_async_session()`.
* **Auto-Commit / Rollback**: If a repository write or database operation fails mid-transaction, SQLAlchemy triggers a rollback to avoid partial writes. On success, the session commits automatically.

---

## 8. Testing Strategy

We verify the storage layer using integration tests at `tests/integration/test_postgres_repository.py`:
* **CRUD Assertions**: Ensures insert, update, retrieve, and delete operations map domain entities correctly.
* **Existence Verification**: Verifies `exists()`, `find_by_url()`, and `find_by_id()` lookup paths.
* **Bulk Operations**: Asserts `bulk_insert()` and `bulk_upsert()` perform write operations in a single database transaction.
* **Transaction Rollback**: Forces mock failure states to verify that changes are rolled back on error.

---

## 9. Future Improvements

* **Connection Pool Tuning**: Adapt max connections, overflow limits, and recycle configurations dynamically to match production worker load.
* **Soft Deletes**: Introduce soft delete indicators on tables to preserve historical data audits.
* **Database Migrations**: Automate incremental DDL table changes using Alembic migrations.
