# Internal System Flow: GET /health

This document describes the request execution flow of the AI Shopping Assistant backend, tracing the sequence of events from booting Uvicorn to delivering the health check JSON payload.

---

## 1. Sequence Diagram

```
Developer   Uvicorn    FastAPI    session.py   AsyncEngine   asyncpg    PostgreSQL
   │           │          │           │             │           │           │
   ├─ Boot ───►│          │           │             │           │           │
   │           ├─ Load ──►│           │             │           │           │
   │           │          ├─ Import ─►│             │           │           │
   │           │          │           ├─ create ───►│           │           │
   │           │          │           │             ├─ connect ─►│           │
   │           ◄─ Ready ──┤           │             │           │           │
   │           │          │           │             │           │           │
   ├────── GET /health ──►│           │             │           │           │
   │           │          ├─ check ──►│             │           │           │
   │           │          │           ├─ execute ──►│           │           │
   │           │          │           │             ├─ SQL ────►│           │
   │           │          │           │             │           ├─ SELECT 1►│
   │           │          │           │             │           │◄─ 1 ──────┤
   │           │          │           │             │◄─ Row ────┤           │
   │           │          │           │◄─ Success ──┤           │           │
   │           │          │◄─ JSON ───┤             │           │           │
   │           ◄─ JSON ───┤           │             │           │           │
   ◄─ JSON ────┤          │           │             │           │           │
```

---

## 2. Request Processing Flowchart

```
[Start: Developer types uv run uvicorn]
               │
               ▼
[Uvicorn loads src/main.py]
               │
               ▼
[Instantiates FastAPI app = FastAPI()]
               │
               ▼
[Registers @app.get("/health") handler]
               │
               ▼
[Developer triggers HTTP GET /health]
               │
               ▼
[FastAPI triggers health_check() function]
               │
               ▼
[Calls check_db_health() in session.py]
               │
               ▼
[Pulls connection from SQLAlchemy Pool]
               │
               ▼
[Compiles SQL SELECT 1 via AsyncEngine]
               │
               ▼
[asyncpg opens binary TCP connection socket]
               │
               ▼
[PostgreSQL parses and executes query]
               │
               ▼
[Returns row payload to host machine]
               │
               ▼
[FastAPI returns JSON response with status=healthy, ping=true]
```

---

## 3. Call Hierarchy & Module Dependencies

### Call Hierarchy:
1. `Uvicorn ASGI Loop`
2. `FastAPI Middleware & Routing`
3. `src.main.health_check()`
4. `src.infrastructure.db.session.check_db_health()`
5. `SQLAlchemy Connection Pool checkout`
6. `SQLAlchemy Async Connection Execute`
7. `asyncpg Connection Protocol Query`

### Module Dependency Graph:
```
           [src/main.py]
                 │
                 ▼
 [src/infrastructure/db/session.py]
                 │
                 ▼
    [src/config/settings.py]
                 │
                 ▼
         [Pydantic Core]
```

---

## 4. Initialization & Execution Sequence

### Which File Executes First?
* **`src/main.py`**: When Uvicorn loads `src.main:app`, Python imports `src/main.py`, executing module-level imports and instantiating the FastAPI application.

### Which Function Executes First?
* **`get_settings()`** in `src/config/settings.py`: Executed on startup to load configuration variables from the environment and `.env`.

### Which Object Gets Created First?
* **`Settings`**: Built by Pydantic during the import phase of `settings.py`.

---

## 5. Subsystem Internals

### Dependency Injection
Dependencies are injected using FastAPI's routing system (e.g. `Depends()`) or class constructors, allowing developers to swap database connections or repositories during testing.

### How SQLAlchemy Creates the Engine
SQLAlchemy calls `create_async_engine()` in `src/infrastructure/db/session.py` to instantiate the global `AsyncEngine` singleton. The engine manages SQL compilers, dialect translations, and the connection pool.

### How `asyncpg` Communicates with PostgreSQL
`asyncpg` opens a TCP socket connection directly to PostgreSQL, bypassing DBAPI constraints. It uses PostgreSQL's front-end/back-end protocol v3.0 to send commands as binary payloads.

### How PostgreSQL Executes `SELECT 1`
1. **Parser**: Checks query syntax.
2. **Optimizer**: Creates a simple plan to return a constant value (`1`).
3. **Execution Engine**: Generates a single-row result set containing `1`.
4. **Network Protocol**: Sends the result row back over the open TCP socket.

### How Response Returns to FastAPI
* `asyncpg` reads the socket stream, parses the result row, and returns it to SQLAlchemy.
* SQLAlchemy closes the session, returning the connection back to the connection pool.
* FastAPI serializes the data into a JSON response payload:
  ```json
  {
      "status": "healthy",
      "ping": true
  }
  ```
