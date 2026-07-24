# System Architecture: Phases 1 to 5
## AI Shopping Assistant Backend

This document details the software architecture, technology decisions, design patterns, and request execution flows for the AI Shopping Assistant backend repository (Phases 1 through 5).

---

## 1. Project Overview

The backend acts as the core orchestration, scraping runtime, persistence, and querying API hub for the distributed AI Shopping Assistant platform. 

### Core Purposes:
* **Orchestration**: Runs worker pools that schedule and execute page fetches.
* **Extraction**: Collects raw payloads and parses product listings, specs, and price trends.
* **Storage**: Maintains structured records using a normalized PostgreSQL schema.
* **Query API**: Exposes clean interface endpoints to downstream search engines, AI helpers, and copilots.

---

## 2. High-Level Architecture

The backend follows an async-first architecture running on the host system or inside Docker.

```
┌───────────┐
│ Developer │
└─────┬─────┘
      │ CLI Command (e.g., uv run uvicorn)
      ▼
┌───────────┐
│  FastAPI  │ (Exposes HTTP routes & handles ASGI lifecycle)
└─────┬─────┘
      │ Loads settings
      ▼
┌───────────┐
│Settings/Env│ (Loads configuration options from .env)
└─────┬─────┘
      │ Initializes
      ▼
┌───────────────┐
│SQLAlchemy Async│ (Declarative models & transactional context)
└─────┬─────────┘
      │ Leverages asyncpg driver
      ▼
┌───────────┐
│  asyncpg  │ (Handles async TCP binary connections)
└─────┬─────┘
      │ Communicates via port 5432
      ▼
┌───────────────────┐
│ PostgreSQL Docker │ (Maintains relational storage)
└───────────────────┘
```

---

## 3. Component Diagram

```
           ┌──────────────────────────────────────────────┐
           │                   FastAPI                    │
           │ (HTTP routing, validation, & endpoint rules) │
           └──────┬──────────────┬──────────────┬─────────┘
                  │              │              │
                  ▼              ▼              ▼
           ┌────────────┐ ┌────────────┐ ┌──────────────┐
           │   Logging  │ │   Config   │ │ Health Check │
           └────────────┘ └────────────┘ └──────────────┘
                  │              │              │
                  └──────────────┼──────────────┘
                                 ▼
                         ┌──────────────┐
                         │   Database   │
                         └──────┬───────┘
                                │ (Eager loading migrations)
                                ▼
                         ┌──────────────┐
                         │   Alembic    │
                         └──────────────┘
```

### Components:
* **FastAPI**: Main gateway handling endpoint requests.
* **Configuration**: Structured settings powered by `pydantic-settings`.
* **Logging**: Structured logger tracking async operations.
* **Database**: Holds connections and controls queries.
* **Alembic**: Runs database migration scripts.
* **Health Check**: Executes diagnostics across database links and workers.

---

## 4. Layered Architecture

The project conforms to Clean Architecture boundaries:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│    (HTTP API Routes, Typer CLI entrypoints, CLI commands)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
│         (Pipeline execution, scrapers, data parsers)        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                     │
│        (SQLAlchemy Engines, Settings loaders, Loggers)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Persistence Layer                       │
│     (Product Repositories, ORM Models, Database Tables)     │
└─────────────────────────────────────────────────────────────┘
```

### Responsibilities:
* **Presentation**: Validates client input and parses request payloads.
* **Application**: Runs extraction rules and schedules scraper workers.
* **Infrastructure**: Handles database configuration and connection pools.
* **Persistence**: Saves records, maps ORM tables, and executes queries.

---

## 5. Database Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PostgreSQL Docker                        │
│ ┌───────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│ │  ProductORM   │  │ SpecificationORM │  │  PriceHistoryORM   │ │
│ └───────▲───────┘  └────────▲─────────┘  └─────────▲──────────┘ │
└─────────┼───────────────────┼──────────────────────┼────────────┘
          │                   │                      │
          └───────────────────┴──────────────────────┘
                              │
                    ┌──────────────────┐
                    │  Session Factory │ (async_sessionmaker)
                    └─────────▲────────┘
                              │
                    ┌──────────────────┐
                    │ Connection Pool  │ (pool_size=10, max_overflow=20)
                    └─────────▲────────┘
                              │
                    ┌──────────────────┐
                    │   AsyncEngine    │ (SQLAlchemy AsyncEngine)
                    └──────────────────┘
```

* **Docker Container**: Runs isolated PostgreSQL 16 server.
* **Database**: Relational database storing product schemas.
* **Connection Pool**: Maintains open sockets to avoid database handshake overhead.
* **Session Factory**: Generates async sessions for queries.
* **Engine**: Directs internal SQL compilation.

---

## 6. Request Flow (`GET /health`)

```
 [Client]    [FastAPI]    [session.py]    [AsyncEngine]    [PostgreSQL]
    │            │             │                │               │
    ├─ GET /health ───────────►│                │               │
    │            │             ├─ select(1) ───►│               │
    │            │             │                ├─ (SELECT 1) ─►│
    │            │             │                │◄─ (Result 1) ─┤
    │            │             │◄─── (OK) ──────┤               │
    │            │◄── (OK) ────┤                │               │
    │◄─ 200 OK ──┤             │                │               │
```

1. **Client**: Issues a `GET /health` request.
2. **FastAPI**: Receives the request and calls the `/health` controller.
3. **session.py**: Opens a database connection context using `check_db_health()`.
4. **AsyncEngine**: Compiles a simple health query (`SELECT 1`).
5. **PostgreSQL**: Runs the query and returns `1`.
6. **Response**: FastAPI formats the test details and returns a `200 OK` JSON response.

---

## 7. Folder Architecture

The folder structure is organized to separate domain logic from infrastructure details:

```
ai_shopping_assistant/
├── alembic/                 # Alembic migration scripts and environment configurations
├── docs/                    # System diagrams and guides
├── src/                     # Core application codebase
│   ├── cli/                 # Typer command line interface commands
│   ├── collectors/          # Scraper collectors and parsers
│   ├── config/              # Configuration files
│   ├── core/                # Core loggers, metrics, and exceptions
│   ├── domain/              # Clean Domain Models and Enums
│   ├── engine/              # Main scraper orchestration engine
│   ├── frontier/            # URL frontier management
│   ├── infrastructure/      # Infrastructure files
│   │   └── db/              # In-memory database repositories
│   ├── interfaces/          # Port interfaces and abstract repositories
│   ├── mappers/             # Domain-to-ORM and ORM-to-Domain mappers
│   ├── orm/                 # SQLAlchemy 2.0 ORM models
│   ├── pipeline/            # Scraping pipeline stages
│   ├── quality/             # Data quality assessors
│   ├── repositories/        # Database repositories
│   │   └── postgres/        # PostgresProductRepository implementation
│   ├── scheduler/           # Scraping execution scheduler
│   ├── search/              # Search engine index and filter logic
│   ├── workers/             # Concurrent queue execution worker pools
│   └── main.py              # Application entrypoint (exposes FastAPI and Typer)
├── tests/                   # Test suite
│   ├── integration/         # Integration tests
│   └── unit/                # Unit tests
├── pyproject.toml           # Project dependencies and configuration
└── test_db.py               # Standalone database health checker
```

---

## 8. Technology Decisions

### Why FastAPI?
FastAPI leverages Python's `async/await` syntax for high-performance requests. It also generates automatic OpenAPI schema definitions from Pydantic types.

### Why asyncpg?
`asyncpg` is a fast asynchronous PostgreSQL driver for Python. It bypasses DBAPI protocols to communicate directly over PostgreSQL's binary protocol, maximizing throughput.

### Why SQLAlchemy Async?
SQLAlchemy 2.0 provides type-safe queries, transaction lifecycle management, and relationship loading (e.g. `selectinload`), while keeping queries asynchronous.

### Why Alembic?
Alembic automates database migrations, enabling developers to update schemas incrementally without manual SQL interventions.

### Why Docker?
Docker isolates the PostgreSQL database, providing a consistent local environment that matches staging and production configurations.

### Why uv?
`uv` is a fast Python packaging tool written in Rust. It accelerates dependency installation and locks precise package versions.

---

## 9. Connection Lifecycle

```
[App Startup] ──► [Engine Instantiation] ──► [Connection Pool Initialization]
                                                         │
                                                         ▼
[JSON Response] ◄── [Session Disposal] ◄── [Query execution] ◄── [Session Checkin]
```

1. **App Startup**: Uvicorn starts the FastAPI application.
2. **Engine Instantiation**: SQLAlchemy creates the global `AsyncEngine` singleton.
3. **Connection Pool**: Pre-warms the database connection pool on startup.
4. **Session Checkin**: Endpoint triggers check out a connection from the pool.
5. **Query Execution**: Executes SQL commands asynchronously.
6. **Session Disposal**: Closes the session and returns the connection back to the pool.
7. **Response**: FastAPI serializes the data and returns the HTTP response.

---

## 10. Future Architecture

The system is designed to support the following services as the platform scales:

```
                               ┌─────────────┐
                               │ FastAPI API │
                               └──────┬──────┘
                                      │
                                      ▼
┌──────────────┐               ┌─────────────┐               ┌─────────────┐
│  AI Engine   │◄─────────────►│   Services  │◄─────────────►│   Scrapers  │
└──────────────┘               └──────┬──────┘               └─────────────┘
                                      │
                                      ▼
┌──────────────┐               ┌─────────────┐               ┌──────────────┐
│Recommendation│◄─────────────►│ Repositories│◄─────────────►│Background Wkr│
└──────────────┘               └─────────────┘               └──────────────┘
```

* **Repositories**: Abstract away data storage interfaces.
* **Services**: Encapsulate business logic like price notifications.
* **Authentication**: Secures endpoints using OAuth2 and JWT.
* **Scrapers**: Fetch data in the background and write to the database.
* **AI Engine**: Runs product deduplication and model parsing.
* **Recommendation System**: Suggests products based on price trends.
* **Background Workers**: Run cron jobs for scheduling crawlers.

---

## 11. Production Readiness

* **Connection Pooling**: Reuses connections to prevent port exhaustion.
* **Scalability**: Decoupled components make it easy to migrate services to independent microservices.
* **Maintainability**: Clear division of layers simplifies code updates.
* **Dependency Injection**: Promotes testability by allowing developers to swap repositories or database instances.
* **Logging & Config**: Timezone-aware structured logging and environment settings help with troubleshooting.
* **Error Handling**: Custom exceptions wrap driver errors to insulate business services from database failures.
