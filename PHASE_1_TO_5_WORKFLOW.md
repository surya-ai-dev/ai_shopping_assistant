# Internal System Workflows: Phases 1 to 5
## AI Shopping Assistant Backend

This document details the step-by-step internal execution workflows of the AI Shopping Assistant backend system.

---

## 1. Application Startup (`uv run uvicorn src.main:app --reload`)

When a developer starts the application on the host machine, the following sequence executes:

1. **Package Resolution**: `uv` checks `pyproject.toml` and `uv.lock` to load the dependencies from the virtual environment (`.venv`).
2. **Uvicorn Initialization**: Uvicorn is loaded as the ASGI server. It parses the target path parameter `src.main:app`.
3. **Module Loading**: Uvicorn loads `src/main.py` which:
   * Instantiates the `FastAPI` instance: `app = FastAPI(...)`.
   * Imports configuration, session, and endpoint route controllers.
4. **Server Binding**: Uvicorn binds to the configured local port (defaulting to `8000`) and starts listening for HTTP traffic.

---

## 2. FastAPI Startup Lifecycle

FastAPI manages startup events using lifespan context managers or event hooks:

```
[Uvicorn Starts] ──► [Lifespan Context Triggered] ──► [Initialize Connection Pool]
                                                               │
                                                               ▼
[HTTP Listening] ◄── [Start Prometheus Exporter] ◄── [Register Endpoint Routes]
```

1. **Lifespan Initialization**: The application context initializes before Uvicorn begins listening for requests.
2. **Global Singletons**: Initializes global singletons (like the database `AsyncEngine` connection pool) to prevent query lag.
3. **Observability**: Boots metrics servers (like the Prometheus exporter running on port `8000`).
4. **Routing Registration**: Registers route endpoints (e.g., `GET /health`) and starts listening for client requests.

---

## 3. Configuration Loading

Settings are loaded dynamically using Pydantic:

```
[System Environment] 
         │ (Overrides)
         ▼
    [.env File] ──► [settings.py (Pydantic Settings)] ──► [config.py (Build URL)]
```

1. **Loading `.env`**: Pydantic's `BaseSettings` looks for a `.env` file in the project root.
2. **Setting Overrides**: System environment variables take precedence over values in the `.env` file.
3. **DATABASE_URL Building**: The `DatabaseConfig` class in `src/database/config.py` processes the raw connection string:
   * Parses credentials: `scraper_user` and `scraper_password`.
   * Validates the driver dialect: converts `postgresql://` to `postgresql+asyncpg://` to support async drivers.

---

## 4. Database Initialization

Database connections are managed by SQLAlchemy:

* **Engine**: The `AsyncEngine` (created via `create_async_engine()`) handles SQL compiling and connection pools.
* **Connection Pool**: The pool maintains open connections to the database using `pool_size=10` and `max_overflow=20` to avoid connection handshake overhead.
* **Session Factory**: `async_sessionmaker` creates short-lived `AsyncSession` contexts to manage transaction boundaries.

---

## 5. Health API Workflow

The `/health` endpoint executes the following query flow:

```
[Browser Client]
       │ HTTP GET /health
       ▼
[src/main.py] (app.get("/health"))
       │ Invokes
       ▼
[src/infrastructure/db/session.py] (check_db_health())
       │ Checks out connection
       ▼
[SQLAlchemy AsyncEngine]
       │ Compiles SELECT 1
       ▼
[asyncpg Driver]
       │ Sends binary packet
       ▼
[PostgreSQL Database]
       │ Evaluates and returns 1
       ▼
[JSON HTTP Response] (status: "healthy")
```

### Functions Involved:
* `health_check()` in `src/main.py`: Handles HTTP routing.
* `check_db_health()` in `src/infrastructure/db/session.py`: Manages the database connection context.
* `get_async_engine()` in `src/infrastructure/db/session.py`: Retrieves the active engine.
* `execute()` on `AsyncSession`: Sends the query string to the database.

---

## 6. Alembic Workflow

Alembic manages database migrations:

### `alembic current`
* Reads the configuration from `alembic.ini`.
* Initializes the python environment in `alembic/env.py`.
* Queries the `alembic_version` table in the database to check the current database schema revision.

### `alembic upgrade head`
* Computes the migration pathway from the current revision to the latest version in `alembic/versions/`.
* Connects asynchronously using `async_engine_from_config` in `alembic/env.py`.
* Runs all pending migration scripts sequentially, updating the `alembic_version` table when complete.

---

## 7. Docker Workflow

```
[Windows Host Shell] ──────► [Docker Desktop (WSL2)] ──────► [Alpine Container]
         │                              │                           │
  docker compose up              Port Bind 5432              Mounts Data Vol
         │                              │                           │
         ▼                              ▼                           ▼
[Connects to localhost:5432] ──► [Forwards to Container] ──► [Starts Postgres 16]
```

1. **Starting PostgreSQL**: Running `docker compose up -d` tells Docker to read `docker-compose.yml`, mount the local `postgres_data` volume, and start the PostgreSQL 16 container.
2. **Port Mapping**: Docker binds port `5432` of the container to port `5432` of the host loopback interface.
3. **Application Routing**: The host Python application connects to `localhost:5432`. Docker Desktop's port forwarder intercepts the traffic and routes it to the database container.

---

## 8. Application Startup Sequence

When booting, the Python runtime loads modules in the following order:

1. **`src/config/settings.py`**: Loads environment variables.
2. **`src/core/logging.py`**: Configures the structured logger.
3. **`src/database/base.py` / `src/orm/models.py`**: Registers database metadata and models.
4. **`src/database/connection.py`**: Initializes the database engine.
5. **`src/database/session.py`**: Sets up session factories.
6. **`src/mappers/product.py`**: Registers domain mappers.
7. **`src/repositories/postgres/product.py`**: Exposes repository database operations.
8. **`src/cli/main.py`**: Registers Typer shell commands.
9. **`src/main.py`**: Launches the FastAPI and Typer application endpoints.

---

## 9. Shutdown Workflow

FastAPI executes the following steps during application shutdown:

1. **Lifespan Termination**: Triggers shutdown hooks.
2. **Session Cleanup**: Closes all active database sessions.
3. **Engine Disposal**: Disposes of the database engine:
   ```python
   await engine.dispose()
   ```
4. **Connection Pool Cleanup**: Closes all open connection pool sockets to prevent leaks.

---

## 10. Current Working State

The following components are completed and verified:
* **Database Connection Layer**: Configured connection pools and async sessions.
* **ORM Schema Mapping**: Defined master tables and relations.
* **Bidirectional Mapper**: Maps objects between domain schemas and ORM records.
* **PostgresRepository**: Implements all repository query operations.
* **ASGI API Bootstrap**: Exposes a FastAPI application in `src/main.py` that checks database health.
* **Integration Tests**: Tests database queries and transaction rollbacks.
