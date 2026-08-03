# AI Platform Architecture: AI Shopping Decision Assistant
## Version 1.0.0 — Production Blueprint

This document details the software architecture, design patterns, security layers, request lifecycles, and future extension roadmaps for the AI Shopping Decision Assistant platform. 

---

## 1 Project Vision

### Purpose of the AI
The AI Shopping Decision Assistant is a production-grade, domain-specific advisor designed to help users navigate complex purchase decisions for high-consideration consumer electronics, specifically **Laptops** and **Mobile Phones**. High-consideration products represent purchases where purchase friction is high due to numerous technical specifications, volatile pricing, varied user reviews, and product configurations. The platform provides objective, data-driven advice, specifications parsing, real-time comparison tables, and price history tracking.

### Why This is Not a Chatbot
Traditional chatbots operate as open-ended conversational interfaces that rely on text similarity and generic Large Language Model (LLM) knowledge. They suffer from context drift, hallucinate specifications, lack access to real-time structured data, and output unverified claims.
By contrast, this is an **AI-Driven Decision Support System**:
1. **Deterministic Execution**: The LLM is used as an orchestration and summarization tool, not as the system of record or primary database.
2. **Strict Tool Binding**: The assistant cannot answer questions about pricing or specifications using its parametric memory. It must query the Tool Registry, which pulls structured facts from the backend database.
3. **Structured Schemas**: Inputs and outputs are strictly validated using Pydantic, ensuring that user responses contain verified product model numbers, actual spec details, and true merchant links.
4. **Structured Outcomes**: Rather than engaging in general discussion, the system targets discrete shopping intents (e.g., generating side-by-side matrices, summarizing pros/cons of reviews, and verifying if a laptop has a specific port type).

### Business Goals
* **Conversion Optimization**: Lower the barrier to purchase by resolving specifications-based anxiety and highlighting verified price drops.
* **User Retention**: Build user trust by providing objective, unbiased, merchant-independent recommendations and price-tracking capabilities.
* **Cost Efficiency**: Minimize inference fees by routing simple questions (e.g., product lookups or greetings) to small local models (Ollama) and reserving expensive reasoning models (Claude/Gemini/OpenAI) for complex comparison tasks.
* **Extensibility**: Establish a plug-and-play architecture where new scrapers, database repositories, and model providers can be integrated with zero downtime.

### User Goals
* **Objective Fact Synthesis**: Avoid scanning dozens of websites, reading promotional blogs, or watching long video reviews to find technical specifications.
* **Optimized Budgets**: Easily check price histories, understand if a current deal is a true discount, and register for price drop notifications.
* **Use-Case Mapping**: Input qualitative requirements (e.g., "I need a laptop for video editing that fits in a backpack") and receive structured options with technical explanations.

---

## 2 Scope

### Supported Categories
* **Laptop**: Notebook PCs, gaming laptops, ultrabooks, Chromebooks, and 2-in-1 convertible devices.
* **Mobile Phone**: Smartphones, basic mobile phones, and cellular-enabled devices.

### Unsupported Categories
* **Everything Else**: All other consumer electronics (e.g., tablets, smartwatches, monitors, desktop computers, components like GPUs/CPUs, televisions) and non-electronic categories (e.g., clothing, groceries, household items).

### Why Scope is Intentionally Limited
1. **Schema Integrity**: Technical specifications for laptops (CPU cores, TDP, RAM speed, NVMe slots, display NITs) and mobile phones (SoC, camera sensor size, optical zoom, battery charging speed, band support) are highly detailed and structured. Attempting to parse, store, and validate schemas for arbitrary categories (e.g., apparel sizes, food ingredients, monitor display stands) would degrade database performance and break repository layers.
2. **Context Window Efficiency**: LLM prompts require strict structuring. By limiting the domain to two categories, we can define highly optimized formatters that fit multiple comparison sheets into small token footprints.
3. **Scraping Precision**: Web scraper collectors and parser templates are customized to read specs from specific merchants. Limiting categories ensures 99% accuracy in data extraction.
4. **Hallucination Prevention**: Restricting agent boundaries makes output validation deterministic. If the LLM generates a response containing a product outside these two categories, the output validator triggers a rejection event.

---

## 3 Target Users

### Current User
* **Tech-Savvy Researchers**: Shoppers comparing granular specs (e.g., "Find a laptop with an AMD Ryzen 7 7840U, 32GB LPDDR5X RAM, and an OLED panel under $1200").
* **Deal Hunters**: Users checking price-history charts to ensure they are getting a real discount and setting alerts.

### Future Users
* **Non-Technical Buyers**: Users describing needs qualitatively (e.g., "I want a mobile phone for my grandfather. It needs to have a very large screen, long battery life, and easy-to-read text").
* **Corporate IT Procurement**: Small business owners evaluating bulk laptops for office work based on reliability ratings and security specs.

### Usage Scenarios
* **Scenario 1: Analytical Cross-Comparison**: A user wants a side-by-side spec comparison table between the Apple MacBook Air M3 and the Dell XPS 13 Snapdragon X Elite, including weight, battery life estimates, and port layouts.
* **Scenario 2: Real-time Price Verification**: A user finds a phone listed for $699 on a merchant site and asks the assistant, "Is this a good price for the Pixel 8 Pro, or has it been cheaper in the last 30 days?"
* **Scenario 3: Quantitative Review Aggregation**: A user asks, "What are the common criticisms of the Lenovo Legion Pro 5 display?" The system synthesizes sentiment analysis scores from the `product_review` repository.

---

## 4 AI Principles

1. **The LLM is Not the System**: The LLM is a processor, not the runtime. Application state, routing, authorization, and transactional database integrity are managed by Python/FastAPI code. The LLM is only invoked when text generation or semantic extraction is required.
2. **Tool-Driven Execution**: The LLM must not guess. Every piece of product information must be fetched from the database repositories by executing a registered tool. If a tool returns no data, the LLM must state that the product is not in the database rather than inventing specifications.
3. **No Direct SQL Access**: The AI system has no raw database access. Prompt-to-SQL is strictly forbidden. Data extraction must pass through the repository layer using predefined, structured, parameterized query methods in SQLAlchemy ORM. This completely neutralizes SQL injection threats and indexing bypasses.
4. **Security First**: Input sanitization, prompt injection scanning, rate limiting, and output validation must occur outside the LLM environment. Safety is handled at the network and application gateways.
5. **Observability First**: Every step of the request lifecycle must generate trace logs. LLM input/output tokens, execution latency, tool invocation logs, and model performance metrics are gathered automatically.
6. **Everything Measurable**: System utility, accuracy, and operational costs are tracked. System administrators must know the cost-per-query and response latency of every intent path.
7. **Everything Replaceable**: Hard-coded integrations with API providers (e.g. OpenAI) are disallowed. Provider access is abstracted via standard protocols. If OpenAI service fails, the system immediately switches to Gemini or a local Ollama deployment.

---

## 5 Complete System Architecture

```
┌────────────────────────────────────────────────────────┐
│                      Web UI / Mobile                   │
└───────────────────────────┬────────────────────────────┘
                            │ (1. HTTP Request / WebSocket)
                            ▼
┌────────────────────────────────────────────────────────┐
│                     Load Balancer                      │ (Nginx / Traefik)
└───────────────────────────┬────────────────────────────┘
                            │ (2. Route Balancing)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Application                  │ (API endpoints, CORS, JSON parsing)
└───────────────────────────┬────────────────────────────┘
                            │ (3. Invoke Endpoint Controller)
                            ▼
┌────────────────────────────────────────────────────────┐
│                       AI Gateway                       │ (Auth check, Request ID injection, Logging)
└───────────────────────────┬────────────────────────────┘
                            │ (4. Sanitize & Verify Threat)
                            ▼
┌────────────────────────────────────────────────────────┐
│                     Security Layer                     │ (Prompt injection check, Jailbreak blocker)
└───────────────────────────┬────────────────────────────┘
                            │ (5. Filter out-of-scope categories)
                            ▼
┌────────────────────────────────────────────────────────┐
│                    Guardrails Layer                    │ (Category check: Laptop & Mobile Phone only)
└───────────────────────────┬────────────────────────────┘
                            │ (6. Classify Intention)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Intent Classifier                    │ (Identify SEARCH, COMPARE, DETAILS, etc.)
└───────────────────────────┬────────────────────────────┘
                            │ (7. Load active states & history)
                            ▼
┌────────────────────────────────────────────────────────┐
│                    Context Builder                     │ (Combine Memory, User profile, Session data)
└───────────────────────────┬────────────────────────────┘
                            │ (8. Select Optimal Model Client)
                            ▼
┌────────────────────────────────────────────────────────┐
│                      Model Router                      │ (Check cost & complexity -> Select Provider)
└───────────────────────────┬────────────────────────────┘
                            │ (9. Run Plan Execution Graph)
                            ▼
┌────────────────────────────────────────────────────────┐
│                    Planning Engine                     │ (LangGraph DAG coordinator)
└─────┬────────────────────────────────────────────┬─────┘
      │ (10a. Invoke Tool)                         │ (10b. Request LLM Inference)
      ▼                                            ▼
┌───────────────┐                            ┌───────────┐
│ Tool Registry │                            │ LLM Layer │ (Ollama / OpenAI / Claude / Gemini)
└─────┬─────────┘                            └─────▲─────┘
      │ (11. Run DB Query)                         │
      ▼                                            │ (14. Send formatted prompt)
┌───────────────┐                                  │
│  Repository   │                                  │
└─────┬─────────┘                                  │
      ├──────────────────────┐                     │
      ▼                      ▼                     │
┌───────────┐          ┌────────────┐              │
│   Redis   │          │ PostgreSQL │              │
└───────────┘          └─────┬──────┘              │
                             │ (12. Return Data)   │
                             ▼                     │
                       ┌────────────┐              │
                       │ Knowledge  ├──────────────┘
                       │    Layer    │ (13. Render to markdown specs, clean tokens)
                       └────────────┘
                            │
                            │ (15. LLM output generated)
                            ▼
                       ┌────────────┐
                       │  Response  │ (Scan for leakage, check hallucination, model links)
                       │ Validation │
                       └─────┬──────┘
                             │ (16. Log system status & token usage)
                             ▼
                       ┌────────────┐
                       │ Monitoring │ (Prometheus metrics / OpenTelemetry traces)
                       └─────┬──────┘
                             │ (17. Return sanitized payload)
                             ▼
┌────────────────────────────────────────────────────────┐
│                      Web UI / Mobile                   │
└────────────────────────────────────────────────────────┘
```

### Component Breakdown

* **User Client**: Represents the customer-facing frontend. Communicates via REST APIs or persistent WebSockets.
* **Load Balancer**: Manages network routing and performs SSL termination. Distributes requests to available stateless FastAPI container instances.
* **FastAPI Application**: Serves the REST endpoints, handles request validation, handles asynchronous events, and serializes output structures.
* **AI Gateway**: Enforces authentication, assigns standard Correlation IDs to requests, tracks client rate limits, and structures logs.
* **Security Layer**: Evaluates incoming text against vector models or string databases to detect injection exploits, jailbreaks, and harmful prompts.
* **Guardrails**: Intercepts queries containing unsupported terms (e.g., "appliances", "watches") to return a friendly, pre-configured failure response, saving LLM token charges.
* **Intent Classifier**: Maps incoming requests to supported intents. Prevents LLM confusion by structuring the query type before passing it to the planner.
* **Context Builder**: Pulls short-term history, user preferences, and active shopping filters to build the active context frame.
* **Model Router**: Runs dynamic heuristic routing. Selects local, low-latency models for basic inputs, and cloud-hosted reasoning models for complex comparisons.
* **Planning Engine**: Executes a Directed Acyclic Graph (DAG) state machine using LangGraph. Orchestrates state transitions, parallel tool executions, and user-facing updates.
* **Tool Registry**: Manages discovery, registration, schemas, and credentials of target execution functions (Product, Review, Price).
* **Repository**: Standardizes transactions with SQLAlchemy models. Abstracts physical SQL configurations from business logic.
* **Redis**: Acts as the caching layer for database records, session configurations, rate-limit buckets, and short-term chat histories.
* **PostgreSQL**: Relational database storing product listings, specifications, price history logs, merchant endpoints, and user profiles.
* **Knowledge Layer**: Receives database row records from the repository and structures them into markdown data matrices or JSON profiles, pruning redundant tokens.
* **LLM Layer**: Coordinates the unified request structure, maps API outputs, and handles provider failovers (OpenAI, Gemini, local Ollama).
* **Response Validation**: Scans generated text against source documents. Rejects response if product models or price figures do not match source database records.
* **Monitoring**: Records latency metrics, token consumption, model performance, tool failures, and system errors for visualization.

---

## 6 AI Request Lifecycle

```
[User]    [FastAPI]    [Gateway]    [Security]    [Classifier]    [Planner]    [Registry]    [Repository]   [LLM Layer]
  │           │            │            │              │              │            │              │             │
  ├─ Query ──►│            │            │              │              │            │              │             │
  │           ├─ Authent ─►│            │              │              │            │              │             │
  │           │            ├─ Sanitize ─►│              │              │            │              │             │
  │           │            │             ├─ Classify ──►│              │            │              │             │
  │           │            │             │              ├─ Build Plan ─►│            │              │             │
  │           │            │             │              │               ├─ Run Tool ─►│              │             │
  │           │            │             │              │               │             ├─ DB Query ──►│             │
  │           │            │             │              │               │             │◄─ Rows ──────┤             │
  │           │            │             │              │               │◄─ Format ───┤              │             │
  │           │            │             │              │               ├─ Compile Prompt ─────────────────────────►│
  │           │            │             │              │               │◄─ Raw Text ───────────────────────────────┤
  │           │            │             │              │               ├─ Validate Output ─────────────────────────┐
  │           │            │             │              │               │◄─ Checked Response ───────────────────────┘
  │           │◄─ Response ─────────────────────────────────────────────┤
  │◄─ Render ─┤            │            │              │              │            │              │             │
```

### Process Step Definitions

1. **User Request**: User sends a prompt ("Compare the battery capacity of iPhone 15 Pro and Galaxy S24").
2. **Authentication**: FastAPI matches the request's Authorization header to an active user session.
3. **Validation**: API filters out malformed payloads and returns validation errors immediately if necessary.
4. **Guardrails**: Input passes through category validators. If user is asking about "air conditioners", the request terminates with a static response.
5. **Intent Classification**: Classifier detects a `COMPARE_PRODUCTS` intent.
6. **Planner**: Instantiates a comparison execution graph. Defines two parallel steps to fetch specifications, followed by a compilation step.
7. **Tool Execution**: Planner requests the `ProductTool` for both models.
8. **Repository**: Tools use the Product Repository to fetch specification records.
9. **Database**: Relational query executes on PostgreSQL, returning raw records.
10. **Prompt Builder**: The Knowledge Layer converts raw database structures into clean markdown lists, appending the user query and instructions.
11. **LLM**: The system selects the routed provider client (e.g., Gemini Flash), sends the prompt, and receives the raw generated response.
12. **Response Validation**: Validator checks if the text contains any unsupported products or mismatched specifications.
13. **Response**: The validated output is sent to the client as a clean, structured payload.

---

## 7 AI Gateway

### Responsibilities
* **Unified Interface**: Serves as the single API boundary for all agentic services.
* **Metadata Extraction**: Extracts client platform, geographic locale, and language parameters to feed to context builders.
* **Request Correlation**: Generates a standard UUID (e.g., `X-Correlation-ID`) on every incoming request, passing it down the execution stack.
* **Rate Limiting Enforcement**: Ensures client IPs or API keys do not exceed the configured query capacity.

### Request Routing
The gateway routes client requests to designated agent controller microservices based on metadata:
* WebSocket requests for interactive chat run through stateful cluster routers.
* Standard REST lookups (e.g. searching for price histories) route directly to fast HTTP workers.

### Authentication and Security Handshake
Every API payload is evaluated by gateway middleware. It verifies:
* JWT authenticity.
* API key validity.
* Cross-Origin Resource Sharing (CORS) limits.

### Middleware Implementation Pattern
The gateway is structured as a collection of modular ASGI middlewares wrapping the FastAPI router. Middlewares include:
1. `CorrelationIDMiddleware`: Injects tracking headers.
2. `RateLimitingMiddleware`: Integrates with Redis/Rate limiting backend structures.
3. `AuditLoggingMiddleware`: Logs request details, paths, and completion latency.

### Future Scalability
As system concurrency grows, the AI Gateway will transition from FastAPI Python middleware to an independent, cloud-native gateway like **Kong** or **Traefik**. This transition will happen transparently since the API interface definitions remain identical.

---

## 8 Security Layer

### Prompt Injection and Jailbreak Detection
The Security Layer intercepts prompts before passing them to any classification or planning logic. It runs three distinct screening systems:
1. **Keyword/Pattern Scanner**: Scans for standard system jailbreak phrases ("ignore previous instructions", "you are now in developer mode", "output the system prompt").
2. **Vector Space Matcher**: Compares user input vectors against a local vector database containing known prompt injection structures. If cosine similarity exceeds `0.85`, the query is flagged as malicious.
3. **Length and Complexity Sanitizer**: Blocks requests exceeding `4000` characters, unless uploading files, to avoid buffer payload attacks.

### SQL Injection Prevention
Since the AI system uses SQLAlchemy and SQL parameters, SQL injection risk is minimized. To protect the database from semantic exploitation:
* The LLM has no access to run arbitrary queries.
* The system strips keywords like `SELECT`, `DROP`, `ALTER`, `UNION` from raw input variables before passing them to repositories.

### Threat Model
* **Threat 1: Prompt Leakage**: An attacker attempts to retrieve the system prompt. Mitigated by prompt leakage scanners checking output payloads.
* **Threat 2: Over-reliance / Poisoned Scrapes**: The system scrapes a website that contains malicious prompt commands designed to trigger system execution changes. Mitigated by stripping execution syntax in the parsing layer.
* **Threat 3: Resource Exhaustion**: Users submit complex queries repeatedly to run up token bills. Mitigated by strict Redis-backed rate-limits.

### Future Security Improvements
* **Adversarial Red-Teaming Pipeline**: Automated testing suite that submits mutating prompt injections to evaluate system resistance.
* **Secure Sandbox Execution Environment**: Moving tool executions (such as parsers) into isolated Docker runtimes to protect core databases.

---

## 9 Guardrail Layer

### Supported Domain
The assistant operates strictly within the online shopping, specifications, reviews, and price checking domains. 

### Supported Categories
The assistant only permits queries containing entities within:
* **Laptop**: Includes components like processor, graphics card, RAM size, storage, screen refresh rate, port selection, screen resolution.
* **Mobile Phone**: Includes camera, screen size, CPU/SoC, battery life, weight, cellular bands, eSIM support.

### Unsupported Requests
If a query contains references to unsupported categories, the guardrail intercepts it:
* **Example Query**: "What is the best microwave under $200?"
* **Action**: Intercepted immediately by the Guardrail middleware. The system returns a static response: *"I am an expert assistant specialized only in Laptops and Mobile Phones. I cannot assist with microwave requests."*

### Business Rules
* **No Price Guarantees**: The assistant must state that prices are historical and subject to change by merchants.
* **No Defamation**: If a product has poor reviews, the assistant must state the rating figures objectively, avoiding non-professional commentary.

### Response Policy (Graceful Degradation)
If a user prompt is partially out of bounds (e.g. "I want to buy a mobile phone and a desk lamp"), the guardrail sanitizes the query, strips the desk lamp entity, notifies the user of the modification, and fulfills the mobile phone request.

---

## 10 Intent Classification

Intent Classification determines which path a request follows.

| Intent Name | Definition | Input Example |
| :--- | :--- | :--- |
| `SEARCH_PRODUCT` | User searches for devices using specifications or qualitative terms. | "Find a laptop with an Intel Core i7 and 16GB RAM." |
| `COMPARE_PRODUCTS` | User requests a comparison of 2 or more devices. | "Compare the Pixel 8 and Galaxy S24." |
| `PRODUCT_DETAILS` | User requests comprehensive specifications for one device. | "Show me everything about the ThinkPad X1 Carbon Gen 11." |
| `PRICE_HISTORY` | User requests a history of pricing over time. | "What was the cheapest price for the Asus ROG Ally?" |
| `PRICE_DROP` | User asks for active deals or wants to track a price. | "Notify me when the iPhone 15 Pro falls below $900." |
| `REVIEW_SUMMARY` | User requests summaries of reviews or sentiment analysis. | "Summarize what users say about the battery life of Dell XPS 15." |
| `SHOPPING_ADVICE` | User asks qualitative questions about buying choices. | "Should I buy a Chromebook or a Windows ultrabook for college?" |
| `GENERAL_GREETING` | User initiates chat or asks how the system works. | "Hello, what can you do?" |
| `UNSUPPORTED` | Out of scope, malicious, or unparseable input. | "Who won the football game last night?" |

### Intent Extraction Engine
The Intent Classifier runs a routing model (using structured output parsing or a small local classifier). It outputs a structured JSON schema:
```json
{
  "primary_intent": "COMPARE_PRODUCTS",
  "confidence": 0.98,
  "entities": {
    "category": "mobile",
    "products": ["Google Pixel 8", "Samsung Galaxy S24"]
  }
}
```

---

## 11 Context Builder

The Context Builder compiles all relevant data points into a single context payload before prompting the LLM.

```
┌────────────────────────────────────────────────────────┐
│                    Context Builder                     │
└─────┬──────────────┬──────────────┬──────────────┬─────┘
      │              │              │              │
      ▼              ▼              ▼              ▼
┌───────────┐  ┌────────────┐  ┌───────────┐  ┌───────────┐
│  Session  │  │Conversation│  │   User    │  │  Product  │
│  Context  │  │  History   │  │  Context  │  │  Context  │
└───────────┘  └────────────┘  └───────────┘  └───────────┘
```

### Context Types

1. **Session Context**: Holds meta-information about the request (e.g., current timestamp, client platform, geo-location for currency conversions).
2. **Conversation History (Short-Term Memory)**: Contains the last $N$ turns of dialogue. System loads this from Redis using the session ID.
3. **User Context**: Contains user preferences (e.g., preferred operating system, screen size preference, budget limits, store affinity).
4. **Product Context**: Contains specification sheets, reviews summaries, and price logs fetched during the active execution cycle.
5. **Shopping Context**: Contains stateful entities like the user's active cart items and comparison history.

---

## 12 Model Router

The Model Router dynamically selects the most efficient LLM provider depending on query intent and complexity.

```
                      ┌──────────────────┐
                      │   Model Router   │
                      └────────┬─────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
      Simple Intent      Medium Intent      Complex Intent
      (Greetings/Help)    (Search/Details)   (Comparison/Advice)
            │                  │                  │
            ▼                  ▼                  ▼
     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
     │ Local Model │    │ Edge Model  │    │ Cloud Model │
     │ (Ollama)    │    │ (Gemini Fl) │    │ (Claude Son)│
     └─────────────┘    └─────────────┘    └─────────────┘
```

### Model Classification Strategy
* **Simple Intents** (`GENERAL_GREETING`, `UNSUPPORTED`):
  * **Model**: Local Ollama (Qwen 2.5 3B / Llama 3.2 3B).
  * **Rationale**: Fast execution, zero API token cost, low resource overhead.
* **Medium Intents** (`SEARCH_PRODUCT`, `PRODUCT_DETAILS`, `PRICE_HISTORY`, `PRICE_DROP`):
  * **Model**: Gemini Flash, GPT-4o-Mini, or Claude Haiku.
  * **Rationale**: Requires tool parsing and reliable output structures, but doesn't require deep logical reasoning.
* **Complex Intents** (`COMPARE_PRODUCTS`, `SHOPPING_ADVICE`, `REVIEW_SUMMARY`):
  * **Model**: Gemini Pro, Claude 3.5 Sonnet, or GPT-4o.
  * **Rationale**: Requires high reasoning capabilities to compare multi-dimensional specifications and synthesize sentiment patterns without hallucinating.

### Provider Abstraction Layer
The code accesses models through a unified wrapper interface. Developers define a `BaseLLMClient` with methods like `generate()` and `generate_stream()`. If a primary provider (e.g., Gemini) returns a 5xx error or times out, the Router switches to the backup provider (e.g., OpenAI) instantly.

---

## 13 Planning Engine

The Planning Engine orchestrates tool executions and text generation tasks using LangGraph.

### Planner Execution Graph
For complex queries, the system compiles a Directed Acyclic Graph (DAG) containing nodes that represent distinct operations:

```
                  ┌───────────────┐
                  │  Start Node   │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Intent Parser │
                  └───────┬───────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    ┌───────────────┐           ┌───────────────┐
    │  Query Product│           │ Query Reviews │
    └───────┬───────┘           └───────┬───────┘
            │                           │
            └─────────────┬─────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Synthesize    │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  Output Check │
                  └───────────────┘
```

### Plan Execution Types
* **Single Tool Plan**: The classifier selects one tool (e.g., `PriceTool`). The engine runs that tool and formats the response.
* **Multi-Tool Plan**: Runs multiple tools sequentially or in parallel. For a comparison query, the engine launches parallel processes to fetch specification data and price logs before synthesizing.
* **Dynamic Workflow Planning**: The LLM evaluates intermediate outputs to adjust subsequent steps. For example, if a search for a laptop model yields no exact match, the engine modifies the query to search for similar laptop models.

### Failure Handling and Retry Strategy
* **Tool Failure**: If a database repository times out, the planner catches the exception, registers a warning, and attempts to fetch cached data from Redis. If no cache exists, it degrades gracefully by informing the user that the details are currently unavailable.
* **Model Timeout**: System uses a `5-second` timeout threshold for LLM queries. If exceeded, the model router falls back to a secondary provider model.

---

## 14 Tool Registry

The Tool Registry manages executable functions exposed to the agents.

### Core Tools

1. **ProductTool** (`get_product_specs`):
   * **Parameters**: `product_model_id: str`, `category: CategoryEnum`
   * **Returns**: Specifications dictionary.
2. **ReviewTool** (`get_review_summary`):
   * **Parameters**: `product_model_id: str`
   * **Returns**: Aggregated ratings, pros list, cons list, sentiment score.
3. **PriceTool** (`get_price_history`):
   * **Parameters**: `product_model_id: str`, `days: int`
   * **Returns**: Average price, historical high, historical low, discount trend.
4. **RecommendationTool** (`get_top_recommendations`):
   * **Parameters**: `category: CategoryEnum`, `constraints: dict`
   * **Returns**: List of matching products.
5. **WishlistTool** (`modify_user_wishlist`):
   * **Parameters**: `user_id: uuid`, `product_model_id: str`, `action: WishlistActionEnum`
   * **Returns**: Success status.
6. **NotificationTool** (`set_price_alert`):
   * **Parameters**: `user_id: uuid`, `product_model_id: str`, `target_price: float`
   * **Returns**: Notification confirmation.

### Plugin Architecture
Adding new tools requires no changes to the planning engine. Developers create functions in `src/ai_agents/tools/` and register them using a registry decorator:
```python
@register_tool(
    name="get_price_history",
    description="Fetches historical pricing for a specific laptop or mobile phone."
)
async def get_price_history(product_model_id: str, days: int = 30) -> dict:
    ...
```
The decorator registers the function metadata and schema, exposing it dynamically to the LLM agent during the planning phase.

---

## 15 Repository Layer

### AI-to-SQL Separation
The AI platform does not construct, modify, or run raw SQL queries. Instead, it interacts with standard Repository classes.

```
┌──────────────┐     Method Call     ┌───────────────────┐     SQL Query     ┌──────────────┐
│  AI Agent /  ├────────────────────►│    Repository     ├──────────────────►│  PostgreSQL  │
│  Planner     │   (get_by_id)       │ (ProductRepository│   (SELECT ...)   │   Database   │
└──────────────┘                     └───────────────────┘                   └──────────────┘
```

### Why Raw Database Rows Never Go Directly to the LLM
1. **Security Isolation**: Prevents exposure of sensitive database fields (e.g. internal timestamps, soft delete flags, hash keys, user tracking details).
2. **Connection Management**: LLM queries can take seconds. If a connection pool is occupied by transactions waiting on slow LLMs, the database pool quickly exhausts. Repositories open connection sessions, execute optimized queries, close sessions, and return objects, decoupling database connections from inference runtimes.
3. **ORM Decoupling**: Database schemas change. Encapsulating access inside the Repository pattern allows database engineers to update tables, normalize columns, or migrate schemas without breaking agent configurations.

---

## 16 Knowledge Layer

The Knowledge Layer sits between database output structures and LLM prompts. It acts as a sanitizer and serializer.

### Knowledge Formatters
* **ProductFormatter**: Standardizes product specification fields into clean markdown tables, keeping key-value pairs clear and brief.
* **ComparisonFormatter**: Creates markdown matrices comparing laptop or mobile phone specs.
* **ReviewFormatter**: Standardizes raw review objects into a clear, bulleted summary of pros, cons, and rating metrics.

### Token Optimization Techniques
Raw JSON strings contain verbose characters (`{`, `"`, `}`, commas) and redundant metadata. The Knowledge Layer:
* Strips null or default fields.
* Limits review strings to critical snippets.
* Normalizes whitespace.
* Truncates content based on target token budgets, preventing context overflow.

---

## 17 LLM Layer

The LLM Layer handles communication with model interfaces.

```
┌────────────────────────────────────────────────────────┐
│                       LLM Layer                        │
└───────────────────────────┬────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│                   BaseLLMClient (Protocol)              │
└─────┬──────────────┬──────────────┬──────────────┬─────┘
      │              │              │              │
      ▼              ▼              ▼              ▼
┌───────────┐  ┌────────────┐  ┌───────────┐  ┌───────────┐
│  Ollama   │  │   OpenAI   │  │ Anthropic │  │  Gemini   │
│  Client   │  │   Client   │  │  Client   │  │  Client   │
└───────────┘  └────────────┘  └───────────┘  └───────────┘
```

### Standardized Model Interface
Every provider integration inherits from `BaseLLMClient`:
* `async def generate(prompt: str, options: dict) -> LLMResponse`
* `async def generate_stream(prompt: str, options: dict) -> AsyncGenerator[LLMResponse, None]`

### Streaming Support
Streaming is critical for conversational applications to minimize perceived latency. The LLM Layer yields chunk structures in real time, standardizing token formats before transmitting them down the FastAPI ASGI channel.

---

## 18 Memory

The Memory subsystem tracks state across conversational bounds.

### Memory Storage Matrix

| Memory Layer | Storage Media | Lifespan | Purpose |
| :--- | :--- | :--- | :--- |
| **Short-Term Memory** | Redis Cache | 24 Hours | Holds dialogue turns (`UserMessage`, `AssistantMessage`) for active chat sessions. |
| **User Preferences** | PostgreSQL | Permanent | Tracks user platform preferences, budget caps, and brand filters. |
| **Active Cart & Wishlist** | PostgreSQL / Redis | Permanent | Stores products saved by the user. |
| **Long-Term Memory** | Vector DB / PostgreSQL | Permanent | Stores synthesized summaries of user interactions for future advice personalization. |

---

## 19 Response Validation

The Response Validator is the final checkpoint before outputting data to users.

### Validation Pipelines

1. **Hallucination Detection**: Checks names, pricing, and specs in the generated response text against the raw records fetched by the tools. If discrepancies are found, the output is flagged.
2. **Product Validation**: Scans all mentioned laptop and mobile models. If the response contains a model not present in the database, the validator strips it or forces regeneration.
3. **Prompt Leakage & Guardrail Check**: Verifies the response does not expose instructions, prompt structures, or contain toxic content.
4. **Structured Format Verification**: Verifies response conforms to standard layouts (e.g. structured markdown, clear comparison matrices).

---

## 20 Monitoring

Logging and monitoring are built directly into agent execution nodes.

```
┌─────────────────┐     Report Metric     ┌────────────────┐
│  Agent Node     ├─────────────────────►│   Prometheus   │
└────────┬────────┘                      └────────────────┘
         │
         │ Send Spans
         ▼
┌─────────────────┐
│  OpenTelemetry  │
└─────────────────┘
```

### Metrics Tracked
* **Latency**: Time elapsed per gateway middleware run, intent classification step, planning step, tool call, and LLM call.
* **Token Consumption**: Track input, output, and cache-hit tokens per provider.
* **Tool Usage**: Track invocation rates, completion rates, and failure rates per tool.
* **Error Tracking**: Log system crash events, fallback routes, validation exceptions, and API errors.
* **Success Rate**: Log the percentage of requests processed without retries or fallbacks.

---

## 21 Cost Optimization

Operating LLMs at scale is expensive. The platform uses cost optimization strategies:

1. **Intelligent Model Routing**: Routes simpler intents to local models (Ollama) or cheaper cloud endpoints (Gemini Flash/GPT-4o-Mini), reserving premium models for complex reasoning.
2. **Semantic Caching (Redis)**: Compares user queries against previous requests in Redis. If a query is semantically identical, the cached response is served, avoiding LLM costs.
3. **Prompt Compression**: Removes conversational filler from prompt payloads. System instructions are pre-compiled and compressed.

---

## 22 Observability

Full observability is maintained using open standards:

* **OpenTelemetry**: Standardizes instrumentation across all code layers.
* **Prometheus**: Aggregates time-series performance metrics.
* **Grafana**: visualizes latency spikes, request success rates, token usage costs, and tool failure rates.
* **Distributed Tracing**: Standard correlation IDs track transactions from the gateway layer down to database calls and LLM invocations.

---

## 23 Scalability

The architecture is designed to scale horizontally to support multiple concurrent users:

* **Stateless API Design**: FastAPI instances hold no local memory states, storing all session history in Redis and persistent records in PostgreSQL.
* **Asynchronous Database Pools**: Connections use `asyncpg` to support high concurrency without blocking CPU cycles.
* **Horizontal Pod Autoscaling (HPA)**: FastAPI containers run on Kubernetes configurations that scale automatically based on CPU and memory thresholds.
* **Background Worker Processing**: Long-running background processes (like web scraping, parsers, and cron schedule evaluations) run on separate worker processes, protecting the API layer from performance degradation.

---

## 24 Future Multi-Agent Architecture

*Note: This architecture is not implemented in the current phase but is designed for future migration.*

```
                          ┌─────────────────────┐
                          │  Coordinator Agent  │ (LangGraph Orchestrator)
                          └──────────┬──────────┘
                                     │
         ┌───────────────────┬───────┴───────────┬───────────────────┐
         ▼                   ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Search Agent  │   │ Review Agent  │   │ Price Agent   │   │ Planner Agent │
└───────────────┘   └───────────────┘   └───────────────┘   └───────────────┘
```

### Multi-Agent Subsystems
1. **Coordinator Agent**: Receives requests, manages user interaction state, and coordinates tasks among specialized sub-agents.
2. **Search Agent**: Searches the database for product listings, matching spec parameters, and filters.
3. **Review Agent**: Synthesizes and ranks reviews, extracting pros, cons, and user sentiment.
4. **Price Agent**: Evaluates historical price trends and handles price-drop alerts.
5. **Planner Agent**: Compiles recommendations, matches user requirements to specs, and evaluates options.

### Migration Strategy
The current single-agent LangGraph setup will be refactored into a hierarchical state graph. Specialized agents will own sub-graphs, and the coordinator will manage state transitions. The API interfaces, tool definitions, and repository layer will remain unchanged, allowing a clean migration.

---

## 25 Folder Structure

The code for the AI agent platform is located in the `src/ai_agents/` directory:

```
src/ai_agents/
├── __init__.py                # Package initialization and exports
├── config.py                  # Agent-specific configurations and parameters
├── gateway/                   # Gateway routing and authorization
│   ├── __init__.py
│   ├── middleware.py          # CORS, rate limiting, and correlation ID injection
│   └── routing.py             # Route definitions and WebSocket controllers
├── security/                  # Input threat detection
│   ├── __init__.py
│   ├── injection_detector.py  # Prompt injection and jailbreak scanners
│   └── sanitizer.py           # Text sanitization and script stripping
├── guardrails/                # Boundary and category checks
│   ├── __init__.py
│   └── domain_guard.py        # Validates domain scope and category rules
├── intents/                   # Intent classification
│   ├── __init__.py
│   ├── classifier.py          # Intent classification logic
│   └── schemas.py             # Intent output models
├── context/                   # Context compilation
│   ├── __init__.py
│   ├── builder.py             # Compiles history, preferences, and session data
│   └── schemas.py             # Structured context models
├── router/                    # Dynamic model routing
│   ├── __init__.py
│   └── model_router.py        # Logic for selecting LLM providers
├── planner/                   # LangGraph planning engine
│   ├── __init__.py
│   ├── engine.py              # Compiles and runs execution plans
│   ├── graph.py               # Defines LangGraph state graphs and nodes
│   └── state.py               # State definitions and schemas
├── tools/                     # System tools for agents
│   ├── __init__.py
│   ├── registry.py            # Tool registration system and decorators
│   ├── product_tool.py        # Spec query tools
│   ├── review_tool.py         # Review aggregation tools
│   ├── price_tool.py          # Price check tools
│   ├── recommendation_tool.py  # Recommendation matching tools
│   ├── wishlist_tool.py       # Wishlist modifier tools
│   └── notification_tool.py   # Price drop notification tools
├── knowledge/                 # Data serializations for LLMs
│   ├── __init__.py
│   ├── formatters.py          # Formats database models into markdown
│   └── optimizer.py           # Token pruning and truncation utilities
├── llm/                       # LLM client abstractions
│   ├── __init__.py
│   ├── interface.py           # Base client interfaces
│   └── providers/             # Target provider integrations
│       ├── __init__.py
│       ├── factory.py         # Loads target provider client
│       ├── ollama.py          # Ollama client
│       ├── openai.py          # OpenAI client
│       ├── anthropic.py       # Claude client
│       └── gemini.py          # Gemini client
├── memory/                    # Memory managers
│   ├── __init__.py
│   └── manager.py             # Interfaces with Redis and PostgreSQL
├── validation/                # Output verification
│   ├── __init__.py
│   └── validator.py           # Validates generated text formats
└── monitoring/                # Performance instrumentation
    ├── __init__.py
    ├── metrics.py             # Prometheus metrics configuration
    └── tracer.py              # OpenTelemetry tracking instrumentations
```

---

## 26 Design Principles

* **SOLID**: Ensure high modularity:
  * **Single Responsibility**: Every module owns one task (e.g. `domain_guard.py` only handles scope guardrails).
  * **Open/Closed**: The planning engine is open for extension (adding new tools) but closed to modification.
  * **Liskov Substitution**: Different LLM clients must be interchangeable behind the `BaseLLMClient` interface.
  * **Interface Segregation**: Clients only import what they use.
  * **Dependency Inversion**: High-level planners depend on abstract LLM interfaces, not concrete provider APIs.
* **Dependency Injection**: Services and repositories are injected dynamically at runtime.
* **Interface-Driven Design**: Enhances testability. All gateways, memory systems, and provider integrations run behind abstract protocols.
* **Replaceable Providers**: Allows quick provider migrations depending on uptime, cost, and latency metrics.

---

## 27 Future Roadmap

The roadmap detailed below outlines the system phases:

```
Phase 8.1 ──► Phase 8.2 ──► Phase 8.3 ──► Phase 8.4 ──► Phase 8.5
                                                           │
┌──────────────────────────────────────────────────────────┘
▼
Phase 8.6 ──► Phase 8.7 ──► Phase 8.8 ──► Phase 8.9 ──► Phase 8.10
                                                           │
┌──────────────────────────────────────────────────────────┘
▼
Phase 8.11 ─► Phase 8.12 ─► Phase 8.13 ─► Phase 8.14 ─► Phase 8.15
```

### Phase Definitions

#### Phase 8.1: AI Gateway & Provider Interface Definition
Define standard interfaces for model clients (`BaseLLMClient`) and structure the AI Gateway middlewares.

#### Phase 8.2: Database Repository Isolation
Create dedicated database access patterns, ensuring that agent tools only interface with repositories.

#### Phase 8.3: Guardrails & Security Implementation
Implement prompt injection scanners, Cosine similarity checks, and category-enforcing guardrails (Laptops and Mobile Phones).

#### Phase 8.4: Intent Classification Engine
Develop intent parsing logic using small models, configuring schemas to identify target user queries.

#### Phase 8.5: Context Assembly Pipeline
Implement the Context Builder to compile session data, active user settings, and conversation history from Redis.

#### Phase 8.6: Custom Tool Registry
Create the registry decorator and configure tools (`ProductTool`, `ReviewTool`, `PriceTool`).

#### Phase 8.7: LangGraph Planning Engine
Design and build the LangGraph workflow structure. Develop state-machine paths to support simple and complex intents.

#### Phase 8.8: Model Routing Orchestrator
Build the model router to dynamically switch models based on intent classification and complexity.

#### Phase 8.9: Knowledge Serialization Layer
Implement formatting tools (`ProductFormatter`, `ComparisonFormatter`) to serialize DB records into markdown.

#### Phase 8.10: Response Validator
Develop output checking logic to scan for hallucinations, correct formats, and potential prompt leaks.

#### Phase 8.11: Telemetry and Logging Setup
Integrate OpenTelemetry tracing and Prometheus metrics.

#### Phase 8.12: Integration Verification
Conduct end-to-end testing of the pipeline (from FastAPI routing down to LLM generation and output validation).

#### Phase 8.13: Production Stress-Testing
Run load tests to monitor latency, connection pools, memory states, and Redis caching.

#### Phase 8.14: Cost Optimization and Fine-Tuning
Optimize token boundaries, adjust semantic cache hit rates, and refine model selection parameters.

#### Phase 8.15: Multi-Agent Architecture Preparation
Perform final review of interfaces and prepare schemas to migrate to multi-agent configurations.
