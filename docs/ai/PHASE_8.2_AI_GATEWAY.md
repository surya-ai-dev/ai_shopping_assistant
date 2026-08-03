# AI Platform: Phase 8.2 — AI Gateway Layer
## Technical Architecture & System Documentation

This document serves as the long-term technical reference for the AI Gateway layer of the AI Shopping Assistant platform.

---

## 1. Phase Overview

### Purpose
The AI Gateway acts as the single, unified entry point for all incoming client requests directed to the AI Platform. It provides a standardized boundary that isolates presentation controllers (such as FastAPI HTTP or WebSocket routers) from downstream model providers, execution planners, and memory states.

### Why Every Request Must Pass Through the Gateway
* **Uniform Request Lifecycle**: Ensures that tracing variables, transaction telemetry, audit metadata, and latency diagnostics are recorded for every conversation turn.
* **Failure Isolation**: Intercepts unhandled errors, client disconnects, API throttling, and platform crashes, formatting them into standardized JSON error envelopes.
* **Policy Enforcement**: Provides a centralized interceptor chain to inject policies like authentication, rate limiting, and prompt-injection filtering prior to downstream LLM invocations.

---

## 2. Objectives

### Request Normalization
Raw inputs (e.g. prompt string, session parameters) are validated using Pydantic v2. Correlation, tracing, and session IDs are normalized and generated if missing, producing a validated, type-safe `AIRequest` instance.

### Context Creation
System state parameters, request metadata, locale variables, and user session variables are compiled into an `ExecutionContext`. This state acts as the core memory thread container passed through the execution pipeline.

### Pipeline Orchestration
Sequences request preprocessing, context assembly, middleware execution, and output formatting. It structures the flow of data cleanly to enforce strict step execution.

### Response Standardization
Decouples client outputs from the framework. It maps successes and platform exceptions alike into a unified `GatewayResponse` wrapper, capturing latency metrics and serialization contexts cleanly.

---

## 3. Current Request Flow

The execution trace of a client request passing through the gateway is diagrammed below:

```
    User
     │
     ▼
FastAPI Endpoint
     │
     ▼
 AI Gateway  ◄── [ gateway.py ]
     │
     ▼
Request Handler ◄── [ request_handler.py ]
     │
     ▼
Context Builder ◄── [ context_builder.py ]
     │
     ▼
  Pipeline   ◄── [ pipeline.py ]
     │
     ├─► Middleware ◄── [ middleware.py ]
     │      ├─► authenticate()
     │      ├─► check_rate_limits()
     │      ├─► run_security_scan()
     │      └─► run_guardrail_check()
     │
     ▼
Response Handler ◄── [ response_handler.py ]
     │
     ▼
Gateway Response
```

### Stage Explanations
1. **User**: Initiates query (e.g., "Recommend laptops under $1000").
2. **FastAPI Endpoint**: Intercepts the HTTP call, validates auth headers, and passes raw query parameters to the AI Gateway.
3. **AI Gateway**: Receives parameters and initializes timing controls.
4. **Request Handler**: Generates correlation IDs, validates input parameters, and returns an `AIRequest` model.
5. **Context Builder**: Combines request values and session attributes into a stateful `ExecutionContext`.
6. **Pipeline**: Runs request handlers, context builders, and response handlers in sequence.
7. **Middleware**: Executes timing controls and structured log bindings, exposing hooks for rate limiting, auth, security, and guardrails.
8. **Response Handler**: Computes execution latency, maps success payloads or catches exceptions, and serializes them.
9. **Gateway Response**: Returns the standardized `GatewayResponse` envelope.

---

## 4. Folder Structure

The implementation layout for Phase 8.2 is structured as follows:

```
src/ai_agents/
├── gateway/
│   ├── __init__.py            # Module public exports
│   ├── gateway.py             # Facade entrypoint
│   ├── pipeline.py            # Lifecycle orchestrator
│   ├── request_handler.py     # Request parsing and ID generation
│   ├── context_builder.py     # Execution context assembler
│   ├── middleware.py          # Latency timers and extension hooks
│   └── response_handler.py    # Output formatters and error serializers
│
└── tests/
    └── test_gateway.py        # Gateway unit tests suite
```

---

## 5. Components

### `gateway.py` (AIGateway)
* **Purpose**: Facade API entrypoint.
* **Responsibilities**: Exposes the async method `process_request(...)`, instantiating the orchestration pipeline, passing runtime args, and returning a `GatewayResponse`.
* **Future Role**: Remains the single platform endpoint imported by FastAPI router routes.

### `request_handler.py` (AIRequestHandler)
* **Purpose**: Input validation parser.
* **Responsibilities**: Parses parameters, validates string lengths, and generates Request IDs, Conversation IDs, and Trace IDs if missing.
* **Future Role**: Exposes hooks to filter out product categories that are not Laptops or Mobile Phones.

### `context_builder.py` (AIContextBuilder)
* **Purpose**: Stateful context compiler.
* **Responsibilities**: Maps session details, trace parameters, and timestamp details into the `ExecutionContext`.
* **Future Role**: Will load database-backed conversation history logs and store user profiles.

### `middleware.py` (AIGatewayMiddleware)
* **Purpose**: Latency tracking and filter interceptor.
* **Responsibilities**: Tracks execution durations, binds correlation variables, and exposes empty hook signatures (`authenticate`, `check_rate_limits`, `run_security_scan`, `run_guardrail_check`).
* **Future Role**: Coordinates security scanners (Phase 8.3) and guardrails (Phase 8.4) before planners execute.

### `pipeline.py` (AIGatewayPipeline)
* **Purpose**: Process orchestrator.
* **Responsibilities**: Coordinates request processing, context assembly, and exception catching.
* **Future Role**: Directs validated queries to intent classification and planner graphs.

### `response_handler.py` (AIResponseHandler)
* **Purpose**: Output serializer.
* **Responsibilities**: Standardizes outcomes into `GatewayResponse` models, attaches latency metrics, and formats exceptions.
* **Future Role**: Translates internal graph outputs into finalized response payloads.

### `test_gateway.py`
* **Purpose**: Unit testing suite.
* **Responsibilities**: Evaluates request validation, correlation ID generation, context compiling, middleware interceptors, and exception handling.
* **Future Role**: Guarantees gateway behavior remains intact when downstream modules are added.

---

## 6. Architecture Constraints

### Strictly Forbidden Operations
During this phase, the AI Gateway MUST NOT:
1. **Execute Business Logic**: No laptop or mobile comparison decisions.
2. **Access PostgreSQL**: No direct database repository calls.
3. **Access Redis**: No reading or writing to cache instances.
4. **Execute Tools**: No web scrapers or parser tool calls.
5. **Call Planners**: No graph traversal or LangGraph setup.
6. **Call LLMs**: No model requests.
7. **Perform AI Reasoning**: No prompt manipulation or text classification.

### Rationale
Mixing infrastructure logic (ID generation, telemetry, parsing) with business logic (data fetching, LLM prompts) results in an unmaintainable codebase. Decoupling the Gateway ensures that network issues, API latency, and authentication checks are handled independently of the AI model execution.

---

## 7. Middleware Responsibilities

* **Correlation IDs**: Binds Request IDs, Conversation IDs, and Trace IDs into logger contexts.
* **Logging**: Structured logs automatically include contextual trace variables.
* **Latency**: Uses `utils/timer.py` to record total milliseconds elapsed.
* **Hooks**: Declares placeholder hooks to execute future authentication, rate limiting, security scanning, and guardrail verification.

---

## 8. Gateway Lifecycle

The gateway processing sequence runs as follows:
1. **Intake**: FastAPI route controller invokes `AIGateway.process_request(...)`.
2. **Parsing**: `AIRequestHandler` normalizes inputs, generating IDs where missing.
3. **Compilation**: `AIContextBuilder` maps session details into the `ExecutionContext`.
4. **Interception**: `AIGatewayMiddleware` intercepts the request, starts latency timers, and logs execution details.
5. **Downstream Run**: The middleware executes the downstream planner callable.
6. **Serialization**: `AIResponseHandler` computes final latency and returns a standardized `GatewayResponse`.
7. **Exception Handling**: Any error raised during this lifecycle is caught, formatted as a failed `GatewayResponse`, and returned safely to the user.

---

## 9. Testing

### Test Coverage
* **`test_request_handler_validation`**: Validates request parsing constraints.
* **`test_request_handler_missing_ids`**: Verifies generation of unique correlation IDs.
* **`test_context_builder_trace_generation`**: Confirms that context builders correctly attach telemetry traces.
* **`test_gateway_success_pipeline`**: Verifies successful pipeline orchestration and latency tracking.
* **`test_gateway_exception_handling`**: Validates that errors are correctly wrapped into standard failed response envelopes.

### Verification Commands
```bash
# Run gateway tests
uv run pytest src/ai_agents/tests/test_gateway.py

# Verify types
uv run mypy src/ai_agents/

# Audit formatting
uv run ruff check src/ai_agents/
```

---

## 10. Deliverables

* **Orchestration Suite**: `gateway.py`, `pipeline.py`, `request_handler.py`, `context_builder.py`, `middleware.py`, and `response_handler.py`.
* **Testing Infrastructure**: `test_gateway.py` covering success and failure lifecycles.
* **Integration**: Integrated custom logger contexts (`logging.py`) and timer metrics (`utils/timer.py`).

---

## 11. Future Integration

The **Security Layer (Phase 8.3)** will integrate into this gateway with zero changes to request handlers, response envelopes, or core pipeline codes, thanks to the open/closed middleware structure:

1. **Leveraging the Middleware Scan Hook**:
   Inside `src/ai_agents/gateway/middleware.py`, we pre-configured a dedicated hook signature:
   ```python
   async def run_security_scan(self, request: AIRequest) -> None:
       pass
   ```
   In Phase 8.3, developers only need to update this function's body to instantiate and run security scanners (such as prompt injection matching or adversarial classifiers).

2. **Standard Exception Interception**:
   If the security scanner detects an injection or jailbreak attempt, it simply raises a `SecurityException` (defined in `exceptions.py` in Phase 8.1):
   ```python
   raise SecurityException(
       message="Prompt injection exploit pattern detected.",
       error_code="AI_SECURITY_VIOLATION",
       details={"similarity_score": 0.94}
   )
   ```
   The `AIGatewayPipeline` immediately catches the raised exception and directs it to `AIResponseHandler.format_exception`. The handler automatically serializes it into a standardized `GatewayResponse(success=False)` containing the code `AI_SECURITY_VIOLATION` and duration metrics, returning it safely to the client.

---

## 12. Summary

The AI Gateway (Phase 8.2) defines the boundaries and execution parameters of the AI assistant platform. By standardizing request handling, context compilation, middleware orchestration, and response formats, the gateway ensures the platform remains stable, performant, and secure under high-consideration consumer workloads.
