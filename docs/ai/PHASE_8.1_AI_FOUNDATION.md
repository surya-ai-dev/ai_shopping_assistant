# AI Platform: Phase 8.1 — AI Foundation Layer
## Technical Architecture & System Documentation

This document serves as the long-term technical reference for the foundational infrastructure layer of the AI Shopping Assistant platform. 

---

## 1. Phase Overview

### Purpose
The AI Agent Platform is designed to support high-consideration consumer electronics shopping decisions (restricted strictly to **Laptops** and **Mobile Phones**). Phase 8.1 (AI Foundation) establishes the framework-agnostic shared infrastructure. It isolates configuration, custom types, logging interfaces, and domain boundaries from downstream model providers, graph orchestrators, and tool registries.

### Goals
* **Establish Domain Isolation**: Lock product boundaries to prevent context drift and minimize out-of-scope model invocation costs.
* **Define Abstract boundaries**: Force all interaction with model providers, planners, and databases to pass through strict, statically checked Python Protocols.
* **Standardize State and Validation**: Provide Pydantic v2 schemas for request validation, token counts, execution contexts, and custom exception handling.
* **Telemetry readiness**: Build Prometheus collectors and OpenTelemetry hooks to trace and measure executions from day one.

### Why This Layer Exists
AI platforms built without a shared infrastructure layer suffer from tight coupling to single API vendors (e.g., OpenAI API locks), untraced and volatile query latencies, validation leaks, and database connection exhausts. The AI Foundation layer solves this by placing standard interface barriers, custom schemas, and structured logging adapters at the base of the application.

---

## 2. Objectives

### Problems Solved
* **Vendor Lock-in**: Abstracting providers behind `BaseLLMClient` protocols allows swapping APIs or routing to local models with zero code modifications in presentation layers.
* **Database Connection Exhaustion**: Providing strict `BaseMemory` and repository abstractions ensures that slow LLM connections do not hold database connection pools open.
* **Hallucination Vectors**: Defining validation schemas ensures that both inputs and generated outputs are structured, bounded, and validated.
* **Scope Creep**: Restricting product schemas ensures the system rejects irrelevant requests (e.g., household appliances) before they hit planners.

### Responsibilities
* Configures environment variables, feature flags, and timeouts.
* Provides the standard package exceptions hierarchy and structured logging adapter.
* Declares standard protocols for tools, planners, routers, memory, and LLMs.
* Houses utilities for ID generation, text sanitization, and timing.

### Design Philosophy
The system follows **Clean Architecture** boundaries, enforcing unidirectional dependency rules. Infrastructure details (such as FastAPI web endpoints, PostgreSQL database drivers, or local Ollama networks) depend on contract protocols and schemas, never the other way around.

---

## 3. Folder Structure

The complete folder hierarchy created in Phase 8.1 is laid out below:

```
src/ai_agents/
├── __init__.py                # Package public exports
├── README.md                  # Developer manual
├── config.py                  # Settings (BaseSettings)
├── constants.py               # Enums and namespace constants
├── feature_flags.py           # Feature toggle configuration model
├── version.py                 # Core version metadata
├── exceptions.py              # Custom Exception hierarchy
├── logging.py                 # Structured logger adapter
├── dependencies.py            # Dependency injection providers
├── metadata.py                # Telemetry and execution models
├── lifecycle.py               # Startup and shutdown hooks
├── types.py                   # Type aliases and generics
│
├── enums/                     # Platform-wide enums
│   ├── __init__.py
│   ├── category.py            # Enforces laptop/mobile boundaries
│   ├── intent.py              # Intent classifications
│   ├── provider.py            # LLM API providers
│   ├── model.py               # Model size classifications
│   └── tool.py                # Tool categories
│
├── contracts/                 # Abstract contracts (Protocols)
│   ├── __init__.py
│   ├── llm.py                 # BaseLLMClient
│   ├── planner.py             # BasePlanner
│   ├── tool.py                # BaseTool
│   ├── router.py              # BaseModelRouter
│   └── memory.py              # BaseMemory
│
├── schemas/                   # Pydantic v2 schemas
│   ├── __init__.py
│   ├── request.py             # Client request validations
│   ├── response.py            # Response tracking (confidence, citations)
│   ├── context.py             # Stateful ExecutionContext
│   ├── intent.py              # IntentResult mapping
│   └── tool.py                # ToolRequest and ToolResponse
│
├── registry/                  # Registry abstractions
│   ├── __init__.py
│   ├── provider_registry.py   # Resolves BaseLLMClient classes
│   ├── tool_registry.py       # Resolves BaseTool instances
│   └── model_registry.py      # Maps models to ModelSizeEnum
│
├── metrics/                   # Telemetry tools
│   ├── __init__.py
│   ├── collector.py           # Prometheus counters and histograms
│   └── tracing.py             # OpenTelemetry span decorator
│
├── utils/                     # Helper utilities
│   ├── __init__.py
│   ├── ids.py                 # Trace UUID generators
│   ├── timer.py               # Timer context manager
│   └── helpers.py             # Sanitization and token estimators
│
└── tests/                     # Test suite
    ├── test_config.py
    ├── test_schemas.py
    ├── test_interfaces.py
    └── test_utils.py
```

---

## 4. Components

### `config.py` (AIAgentSettings)
* **Purpose**: Manages configuration settings from environment variables.
* **Responsibilities**: Defines models for model temperature, timeout seconds, maximum retry checks, local Ollama URLs, Redis cache servers, and debug flags.
* **Future Usage**: Dynamically loaded at FastAPI application start and used to instantiate LLM clients and memory caches.

### `constants.py`
* **Purpose**: Holds final static values.
* **Responsibilities**: Centralizes string identifiers for categories (`laptop`, `mobile`), intents, and logging names.
* **Future Usage**: Imported by routers, intent classifiers, and logging middleware to avoid manual strings.

### `feature_flags.py` (AIFeatureFlags)
* **Purpose**: Controls active features at runtime.
* **Responsibilities**: Defines flags for `enable_memory`, `enable_guardrails`, `enable_planner`, and `enable_tracing`.
* **Future Usage**: Evaluated in gateway and planner middleware chains to bypass or execute steps.

### `metadata.py`
* **Purpose**: Defines schema parameters for correlation auditing.
* **Responsibilities**: Declares Pydantic models for request footprints, session locales, trace spans, and execution diagnostics.
* **Future Usage**: Attached to execution contexts and logged.

### `lifecycle.py`
* **Purpose**: Application lifecycle hook definitions.
* **Responsibilities**: Exposes `initialize_ai_platform` and `shutdown_ai_platform` async entry points.
* **Future Usage**: Run by FastAPI startup/shutdown lifecycles to initialize client connection pools.

### `logging.py` (AILogger)
* **Purpose**: Adapter wrapper for structured logging.
* **Responsibilities**: Binds request IDs, trace IDs, and durations into `structlog` context variables.
* **Future Usage**: Instantiated by all AI modules to log events.

### `exceptions.py`
* **Purpose**: Defines standard exception hierarchies.
* **Responsibilities**: Provides custom exceptions like `GatewayException`, `LLMException`, `PlannerException`, `ToolException`, and `SecurityException`.
* **Future Usage**: Raised inside gateway pipelines, model adapters, and tool executors.

### `dependencies.py`
* **Purpose**: FastAPI dependency providers.
* **Responsibilities**: Resolves LLM client, router, planner, and memory objects from application state.
* **Future Usage**: Injected into FastAPI route controller endpoints.

### `contracts/`
* **Purpose**: Interfaces representing execution boundaries.
* **Responsibilities**: Defines Protocols like `BaseLLMClient`, `BasePlanner`, `BaseTool`, `BaseModelRouter`, and `BaseMemory`.
* **Future Usage**: Inherited by concrete wrappers (e.g. `OllamaLLMClient`, `LangGraphPlanner`).

### `schemas/`
* **Purpose**: Structural data models.
* **Responsibilities**: Houses schemas for request payloads, response payloads, execution context states, and tool arguments.
* **Future Usage**: Passed between the gateway, planning graph nodes, and clients.

### `registry/`
* **Purpose**: Decoupled container registries.
* **Responsibilities**: Provides registry mappings for model metadata, tool collections, and LLM provider types.
* **Future Usage**: Populated at startup to register available tools and provider clients.

### `metrics/`
* **Purpose**: Operational performance auditing.
* **Responsibilities**: Defines Prometheus collectors and wraps functions with OpenTelemetry spans.
* **Future Usage**: Scraped by Prometheus and Grafana instances.

### `utils/`
* **Purpose**: Foundational code helper routines.
* **Responsibilities**: Generates correlation IDs, measures execution latency in milliseconds, and sanitizes strings.
* **Future Usage**: Imported across all modules.

---

## 5. Architecture Diagram

The relation map of Phase 8.1 foundation elements is detailed below:

```
  ┌────────────────────────────────────────────────────────┐
  │                       config.py                        │
  │            (Loads env, sets feature flags)             │
  └────────┬───────────────────────────────────────┬───────┘
           │                                       │
           ▼                                       ▼
┌────────────────────┐                   ┌───────────────────┐
│     logging.py     │                   │    metadata.py    │
│ (AILogger Wrapper) │                   │  (Trace/Exec MD)  │
└──────────┬─────────┘                   └─────────┬─────────┘
           │                                       │
           ├───────────────────┬───────────────────┤
           ▼                   ▼                   ▼
┌────────────────────┐ ┌───────────────┐ ┌───────────────────┐
│    exceptions.py   │ │   types.py    │ │    constants.py   │
│ (Custom Hierarch)  │ │ (Aliases/Gen) │ │ (Intent/Category) │
└──────────┬─────────┘ └───────┬───────┘ └─────────┬─────────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               ▼
                 ┌───────────────────────────┐
                 │        contracts/         │ (llm, planner, tool,
                 │   (Abstract Protocols)    │  memory, router)
                 └─────────────┬─────────────┘
                               ▼
                 ┌───────────────────────────┐
                 │         schemas/          │ (request, response,
                 │    (Pydantic validation)  │  context, tool, intent)
                 └─────────────┬─────────────┘
                               ▼
                 ┌───────────────────────────┐
                 │         registry/         │ (provider, tool,
                 │    (Registration APIs)    │  model containers)
                 └─────────────┬─────────────┘
                               ▼
                 ┌───────────────────────────┐
                 │   utils/  &   metrics/    │ (latency, tracer,
                 │ (ID gen, sanit, Otel/Prom)│  counters, timers)
                 └───────────────────────────┘
```

---

## 6. Design Principles

* **SOLID**: 
  * *Single Responsibility*: Modules are decoupled (e.g. `exceptions.py` only defines exception structures).
  * *Open/Closed*: Adding new tools or LLM adapters only requires creating concrete subclasses without modifying pipeline orchestrators.
  * *Interface Segregation*: Components reference Protocols (`BaseLLMClient`, `BaseTool`), importing only required parameters.
  * *Dependency Inversion*: Downstream planners depend on abstract contracts.
* **Dependency Injection**: Application services and repositories are injected dynamically at runtime via FastAPI dependencies.
* **Strong Typing**: The codebase maintains strict static typing validated by MyPy (`strict = true` configurations).
* **Pydantic Validation**: Structural validation is handled at runtime by Pydantic v2.
* **Protocol-based Interfaces**: Interfaces run as `Protocol` models, decorated with `@runtime_checkable` for runtime safety.

---

## 7. Testing

The testing suite validates configuration settings, Pydantic constraints, registry mappings, and timing functions.

### Verification Tools
To run static validation, style audits, and unit tests, execute:

```bash
# Run the test suite
uv run pytest src/ai_agents/tests/

# Verify strict type safety
uv run mypy src/ai_agents/

# Audit code formatting and linting rules
uv run ruff check src/ai_agents/
```

---

## 8. Deliverables

* **Package Setup**: `version.py`, `constants.py`, `feature_flags.py`, `config.py`, `metadata.py`, `dependencies.py`, `lifecycle.py`, `types.py`, and `__init__.py`.
* **Platform Enums**: `category.py`, `intent.py`, `provider.py`, `model.py`, and `tool.py` inside `enums/`.
* **Abstract Protocols**: `llm.py`, `planner.py`, `tool.py`, `router.py`, and `memory.py` inside `contracts/`.
* **Pydantic Schemas**: `request.py`, `response.py`, `context.py`, `intent.py`, and `tool.py` inside `schemas/`.
* **Containers Registries**: `provider_registry.py`, `tool_registry.py`, and `model_registry.py` inside `registry/`.
* **Telemetry Monitors**: `collector.py` and `tracing.py` inside `metrics/`.
* **Utilities**: `ids.py`, `timer.py`, and `helpers.py` inside `utils/`.
* **Unit Tests**: Full test suite verifying features inside `tests/`.

---

## 9. Future Integration

Phase 8.2 (AI Gateway) builds directly on this foundation layer:
1. **Pipeline Instantiation**: The gateway uses `dependencies.py` to resolve pipeline handlers and inject client metadata.
2. **Context Compilation**: The gateway context builder pulls session metadata to populate `ExecutionContext` (`schemas/context.py`).
3. **Audits and Exceptions**: The gateway middleware uses `Timer` (`utils/timer.py`) to measure latency and routes errors to standard exceptions (`exceptions.py`), wrapping them into standardized `GatewayResponse` envelopes.

---

## 10. Summary

The AI Foundation layer (Phase 8.1) implements the core infrastructure for the AI Shopping Decision Assistant. It establishes strict category constraints (restricted strictly to **Laptops** and **Mobile Phones**), standardizes request validations, and isolates business logic, ensuring the platform remains modular, scalable, and maintainable.
