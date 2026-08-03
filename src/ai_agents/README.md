# AI Agent Platform Foundation (Phase 8.1)

This package contains the core architectural foundation, interface contracts, Pydantic data schemas, registry containers, and utility wrappers for the AI Shopping Decision Assistant.

## Purpose

The AI Agent platform acts as an expert shopping assistant specialized in **Laptops** and **Mobile Phones**. This foundation sets up the strictly typed interfaces and shared components, ensuring that future agent implementations, LangGraph planning nodes, and external tool plugins remain decoupled, secure, and production-ready from day one.

## Architecture and Design Principles

The platform is designed following **Clean Architecture** and **SOLID** principles:
1. **Interface-Driven Design**: Planners and controllers interact with LLM providers, tool registries, memory databases, and routers via abstract Protocol definitions. This completely avoids hard-coded dependencies.
2. **Strict Domain Boundaries**: Product categories are strictly constrained using `CategoryEnum` (supporting only `laptop` and `mobile`).
3. **Structured Schemas**: All data passed across boundary lines (requests, responses, execution contexts, tool payloads) are strictly validated using Pydantic v2.
4. **Decoupled Repositories**: Agents do not have SQL access. Data lookup tools must access physical databases using standard Repository abstractions.

---

## Folder Structure & Responsibilities

```
src/ai_agents/
├── __init__.py                # Package initialization and public exports
├── README.md                  # Developer manual
├── config.py                  # Environment configurations (BaseSettings)
├── constants.py               # Global final variables (intents, category strings)
├── feature_flags.py           # Core feature flags model
├── version.py                 # Platform version details
├── exceptions.py              # Hierarchical custom exceptions
├── logging.py                 # Structlog logger wrapper with context tracing
├── dependencies.py            # FastAPI Dependency injection wrappers
├── metadata.py                # Telemetry and request metadata models
├── lifecycle.py               # Application startup and shutdown hook placeholders
├── types.py                   # Global type variables and aliases
│
├── enums/                     # Platform-wide enums
│   ├── __init__.py
│   ├── category.py            # Restricted CategoryEnum (laptop, mobile)
│   ├── intent.py              # User request IntentEnum
│   ├── provider.py            # LLM ProviderEnum
│   ├── model.py               # ModelSizeEnum (small, medium, large)
│   └── tool.py                # ToolTypeEnum
│
├── contracts/                 # Abstract contracts (Protocols/Interfaces)
│   ├── __init__.py
│   ├── llm.py                 # BaseLLMClient interface
│   ├── planner.py             # BasePlanner interface (LangGraph runtime)
│   ├── tool.py                # BaseTool interface
│   ├── router.py              # BaseModelRouter interface
│   └── memory.py              # BaseMemory interface
│
├── schemas/                   # Pydantic v2 validation models
│   ├── __init__.py
│   ├── request.py             # Client AIRequest with validations
│   ├── response.py            # Client AIResponse with tokens and confidence
│   ├── context.py             # ExecutionContext holding conversation state
│   ├── intent.py              # IntentResult output mapping
│   └── tool.py                # ToolRequest and ToolResponse schemas
│
├── registry/                  # Empty registries with registration APIs
│   ├── __init__.py
│   ├── provider_registry.py   # Registry mapping providers to BaseLLMClient
│   ├── tool_registry.py       # Registry managing BaseTool instances
│   └── model_registry.py      # Registry mapping model strings to ModelSizeEnum
│
├── metrics/                   # Telemetry, Prometheus trackers, and tracing
│   ├── __init__.py
│   ├── collector.py           # Prometheus counters and histograms
│   └── tracing.py             # OpenTelemetry trace decorators
│
├── utils/                     # General helper utilities
│   ├── __init__.py
│   ├── ids.py                 # Correlation and tracing UUID generators
│   ├── timer.py               # Duration measurement context manager
│   └── helpers.py             # Text sanitization and token estimators
│
└── tests/                     # Unit test suites verifying foundation integrity
    ├── test_config.py
    ├── test_schemas.py
    ├── test_interfaces.py
    └── test_utils.py
```

---

## Extension Strategy

* **Adding a New LLM Provider (Phase 8.11)**:
  Create a client class in `src/ai_agents/llm/providers/` that implements `BaseLLMClient`. Register the class in the `ProviderRegistry` using `registry.register(ProviderEnum.NEW_PROVIDER, NewProviderClient)`.
* **Adding a New Agent Tool (Phase 8.6)**:
  Create a new tool class implementing `BaseTool`. Register the tool instance with the `ToolRegistry` so the planner engine can discover it dynamically during execution.
* **Creating a New Custom Exception**:
  Inherit from `AIException` or one of its child exceptions (e.g. `ToolException`) defined in `exceptions.py`. Ensure you provide a unique `error_code` string for frontend parsing.

---

## Future Implementation Roadmap

* **Phase 8.2: AI Gateway & Security Middleware**: Build ASGI middlewares implementing prompt injection detectors, jailbreak vector check blocks, and rate limiters.
* **Phase 8.3: Guardrails Layer**: Inject domain guards validation schemas to drop non-electronics lookups.
* **Phase 8.4: Intent Classification**: Create structured routers to map prompts to `IntentEnum` values.
* **Phase 8.5: Context Assembly**: Link conversation cache systems (Redis) to the Pydantic `ExecutionContext` compiler.
* **Phase 8.6: Custom Tool Implementations**: Write repository wrappers for specs, prices, and reviews lookup tools.
* **Phase 8.7: LangGraph planning engine**: Build multi-step decision graphs.
