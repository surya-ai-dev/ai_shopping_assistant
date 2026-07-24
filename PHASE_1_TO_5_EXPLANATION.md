# Educational Code Guide: Phases 1 to 5
## AI Shopping Assistant Backend

This document provides a line-by-line and file-by-file explanation of the AI Shopping Assistant backend codebase to help onboarding developers understand how the system works.

---

## 1. Project Directory Structure & Key Files

The following sections explain the purpose, design, execution flow, inputs, and outputs of every key configuration, session, and execution module in the project.

---

## 2. File-by-File Breakdown

### 1. `pyproject.toml`

#### Purpose & Why it Exists
Defines the project metadata, build backend, runtime dependencies, and development groups. It provides a single source of truth for the project environment.

#### Responsibilities
* Configures static package metadata (name, version, description, authors).
* Declares core production dependencies (FastAPI, SQLAlchemy, Playwright, Alembic).
* Declares optional developer dependencies (`pytest`, `ruff`, `mypy`).
* Specifies code formatting and typing rules (Ruff, MyPy).

#### How it Connects to Other Files
* Loaded by **`uv`** to build the virtual environment (`.venv`).
* Used by **`Dockerfile`** to install dependencies in the builder stage.

#### Expected Inputs & Outputs
* **Inputs**: Dependency name declarations.
* **Outputs**: Resolved lockfile (`uv.lock`) and virtual environment packages.

---

### 2. `docker-compose.yml`

#### Purpose & Why it Exists
Orchestrates multi-container execution. It provides a local PostgreSQL database container matching production environments.

#### Responsibilities
* Configures the `postgres` service using the `postgres:16-alpine` image.
* Sets environment variables for credentials (`POSTGRES_USER`, `POSTGRES_PASSWORD`).
* Binds port `5432` of the container to port `5432` of the host.
* Mounts a local volume (`postgres_data`) for data persistence.
* Sets up a health check utilizing `pg_isready`.

#### How it Connects to Other Files
* Resolves variables defined in the `.env` file.
* Integrates with **`Dockerfile`** to compile the `scraper_app` runner service.

#### Expected Inputs & Outputs
* **Inputs**: Environment variable files.
* **Outputs**: Running container instances.

---

### 3. `.env`

#### Purpose & Why it Exists
Stores local environment variables and database credentials. Using a `.env` file separates secrets from the source code.

#### Responsibilities
* Stores development configurations (like database usernames and passwords).
* Defines logging thresholds (`LOG_LEVEL=INFO`).
* Specifies port bindings and metrics endpoints.

#### How it Connects to Other Files
* Loaded automatically by **`Settings`** inside `src/config/settings.py`.
* Interpolated by **`docker-compose.yml`** on startup.

---

### 4. `src/config/settings.py`

#### Purpose & Why it Exists
Defines the application's configuration schema using Pydantic Settings.

#### Responsibilities
* Declares fields for environment variables with type hints.
* Automatically converts string inputs into their appropriate Python types (e.g. converting strings to integers or booleans).
* Provides fallback default values for local development.

#### Key Class: `Settings`
```python
class Settings(BaseSettings):
    ENVIRONMENT: str = Field(default="development")
    POSTGRES_USER: str = Field(default="scraper_user")
    POSTGRES_PASSWORD: str = Field(default="scraper_password")
    POSTGRES_DB: str = Field(default="scraper_db")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://scraper_user:scraper_password@localhost:5432/scraper_db"
    )
```

#### How it Connects to Other Files
* Imported by database engines (`connection.py`) and loggers (`logging.py`) to retrieve configuration options.

---

### 5. `src/infrastructure/db/session.py`

#### Purpose & Why it Exists
Manages the SQLAlchemy asynchronous database connection lifecycle.

#### Responsibilities
* Instantiates the async database engine using the configured `DATABASE_URL`.
* Manages session transactions.
* Exposes a `check_db_health()` diagnostic check to verify database connectivity.

#### Key Functions
* **`get_async_engine()`**: Returns a cached `AsyncEngine` singleton instance to prevent multiple engine creations.
* **`check_db_health()`**: Runs a test query (`SELECT 1`) to check the database connection health.
  ```python
  async def check_db_health() -> dict:
      try:
          engine = get_async_engine()
          async with engine.connect() as conn:
              await conn.execute(text("SELECT 1"))
          return {"status": "healthy"}
      except Exception as exc:
          return {"status": "unhealthy", "error": str(exc)}
  ```

#### How it Connects to Other Files
* Imported by **`src/main.py`** to handle health checks.

---

### 6. `src/main.py`

#### Purpose & Why it Exists
Exposes the application's entrypoint, supporting both the Uvicorn FastAPI server and the Typer CLI commands.

#### Responsibilities
* Instantiates the FastAPI application.
* Declares HTTP route controllers.
* Calls the Typer CLI application if run directly.

#### Key Code Sections
```python
from fastapi import FastAPI
from src.cli.main import app as cli_app

app = FastAPI(title="AI Shopping Assistant Scraper API")

@app.get("/health")
async def health_check() -> dict:
    from src.infrastructure.db.session import check_db_health
    return await check_db_health()

if __name__ == "__main__":
    cli_app()
```

#### How it Connects to Other Files
* **FastAPI**: Imported by Uvicorn to run the API: `uvicorn src.main:app`.
* **Typer CLI**: Imports `app` from `src.cli.main` to run CLI commands: `python -m src.main`.

---

### 7. `test_db.py`

#### Purpose & Why it Exists
A standalone testing script to verify local database connectivity.

#### Responsibilities
* Boots the database configuration.
* Executes a health check.
* Prints connection status outputs and exits with status codes.

#### Execution Code
```python
async def main() -> None:
    health = await check_db_health()
    if health.get("status") == "healthy":
        print("✅ Connected successfully")
        sys.exit(0)
    else:
        print("Error: Database connection failed.")
        sys.exit(1)
```

---

### 8. `alembic/`

#### Purpose & Why it Exists
Manages database schema migrations.

#### Key Files
* **`alembic/env.py`**: Boots the migration environment. It dynamically overrides `sqlalchemy.url` with the `DATABASE_URL` loaded from `settings.py` before running migrations asynchronously.
* **`alembic/versions/`**: Holds migration version scripts.

---

## 3. Dependency Graph

The diagram below shows how files depend on each other:

```
        [.env] ──► [settings.py] 
                       │
                       ├──────────────────────────┐
                       ▼                          ▼
               [connection.py]               [env.py (Alembic)]
                       │                          │
                       ▼                          ▼
               [session.py]                  [PostgreSQL]
                       │                          ▲
                       ├───────────────┐          │
                       ▼               ▼          │
                 [test_db.py]      [main.py] ─────┘
```
