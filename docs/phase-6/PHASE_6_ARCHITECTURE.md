# System Architecture: Phase 6 Database Models
## AI Shopping Assistant Backend

This document details the software architecture, design patterns, and architectural boundaries governing the database models in Phase 6.

---

## 1. High-Level Modular Design

Our backend is built using **Clean Architecture** and **Domain-Driven Design (DDD)** principles. The application is segregated into distinct layers, isolating the core business rules from external technologies like web frameworks, database ORMs, or crawlers.

```
       ┌──────────────────────────────────────────────────────────┐
       │                   Presentation Layer                     │
       │     (FastAPI Routers, Uvicorn Server, CLI Commands)      │
       └───────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
       ┌──────────────────────────────────────────────────────────┐
       │                    Application Layer                     │
       │    (Service Orchestrators, Scrapers, Background Jobs)     │
       └───────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
       ┌──────────────────────────────────────────────────────────┐
       │                  Infrastructure Layer                    │
       │         (SQLAlchemy Engine, Repositories, Redis)         │
       └───────────────────────────┬──────────────────────────────┘
                                   │
                                   ▼
       ┌──────────────────────────────────────────────────────────┐
       │                    Persistence Layer                     │
       │        (PostgreSQL 16, SQLAlchemy Models, Migrations)     │
       └──────────────────────────────────────────────────────────┘
```

### Layer Responsibilities in Phase 6:
* **Persistence Layer (`src/models/`)**: Declares the physical database schema structure using SQLAlchemy ORM. These classes are concrete representations of database tables.
* **Infrastructure Layer (`src/infrastructure/db/`)**: Instantiates the connection pools (`session.py`) and manages physical repositories that perform database operations.
* **Application Layer**: Contains business service logic, orchestrating actions such as adding items to a user's wishlist or checking prices.
* **Presentation Layer**: Exposes endpoints and maps user payloads to database entities.

---

## 2. Dependency Diagram

To prevent dependency cycles (circular imports), imports must strictly flow downwards. The persistence models do NOT import anything from the repositories, service layer, or APIs.

```
                 [alembic/env.py]
                        │
                        ├──────────────────────────┐
                        ▼                          ▼
               [src/models/__init__.py]    [src/infrastructure/db/base.py]
                        │
                        ├──────────────────────────┐
                        │ (Imports all entities)   │
                        ▼                          ▼
               [src/models/user.py]        [src/models/base.py]
               [src/models/product.py]            │
               [src/models/wishlist.py]           ▼
                        │                  [src/models/mixins.py]
                        ▼
               [src/models/enums.py]
```

### Module Loading Sequence:
1. **Bootstrapping**: Alembic loads `alembic/env.py`.
2. **Metadata Registration**: `env.py` imports `src/models/__init__.py`.
3. **ORM Parsing**: Python loads all model files sequentially. Each class inheriting from `BaseModel` automatically registers its schema structure into the centralized `Base.metadata` registry.
4. **Comparison**: Alembic accesses `Base.metadata` to generate migration scripts or execute schema upgrades against PostgreSQL.
