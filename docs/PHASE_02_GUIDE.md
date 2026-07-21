# Phase 2 Guide: Production Collector Framework & Scraping Runtime

This engineering document provides a comprehensive overview of the design, architecture, components, data flows, and code quality specifications implemented during Phase 2 of the AI Shopping Assistant Scraping Platform.

---

## 1. Phase Overview

Phase 2 focuses on building a highly resilient, production-ready, distributed-capable scraping runtime. The core goal is to transition from basic abstract boundaries into high-performance page acquisition, evasion, and extraction pipelines.

### Objectives of Phase 2
* **Resilient Playwright Execution**: Maintain a 3-tier resource pool (Browser, Context, Page) to prevent memory leaks and handle high-throughput crawling.
* **Collector Plugin System**: Build extensible collectors/parsers for Amazon (Mobile Category) and BestBuy (Laptop Category) without introducing hardcoded conditional switching blocks in the central pipeline core.
* **Resilient Network Client**: Implement exponential backoff, delay jitter, user-agent rotation, and connection retry policies to navigate anti-bot protections.
* **Strict Type Safety and Schema Enforcement**: Ensure all extracted attributes are normalized and validated using strict Pydantic v2 domain schemas before persisting them to SQL stores.

### Problems Solved
* **Unstructured Extracted Payloads**: Standardized multi-source raw web structures into normalized Pydantic domain models (`LaptopSpecs`, `MobileSpecs`).
* **Resource Bloat**: Playwright instances are recycled at the context level and cleaned up gracefully under error states, eliminating zombie browser processes.
* **Brittle Parsing**: The addition of a multi-key search resolution layer (`_find_spec`) prevents parsing failures when targets change spec-table labels.

### Scope and Deliverables
* Concrete plugin implementations: `AmazonCollector`/`AmazonParser`, `BestBuyCollector`/`BestBuyParser`.
* Playwright layered resource managers: `LayeredBrowserPool`.
* Advanced network client wrapper: `RequestManager`.
* Extracted database schema integrations: `ProductRepository` and DQA evaluations.
* Comprehensive unit and integration test suite.

---

## 2. Architecture Overview

The system architecture follows clean architecture guidelines. Web interaction, database connectivity, and parsing rules are isolated from the central execution engine (`ScrapePipeline`).

### ASCII Architecture Diagram

```
User (Trigger / Job Scheduler)
        │
        ▼
   ScrapePipeline (Orchestrator)
        │
        ├──────────────────────────┐
        ▼                          ▼
LayeredBrowserPool           RequestManager (Retries / Jitter / UA)
        │                          │
        ├──────────────────────────┘
        ▼
Playwright Active Page
        │
        ▼
Collector.fetch_page() ──► Download Raw HTML ──► FileSystemRawStorage
                                                       │
                                                       ▼
ProductRepository ◄── DQA Assessor ◄── Pydantic ◄── Parser.parse()
(PostgreSQL)         (Thresholds)     (Specs)       (BeautifulSoup)
```

### Component Breakdown
1. **User/Scheduler**: Queues `DiscoveredURL` targets via CLI or job manager.
2. **Collector**: Orchestrates site-specific network paths, listing crawl jobs, and health check actions.
3. **Request Manager**: Resolves rate-limiting tokens, rotating HTTP headers, and backing off on network drops.
4. **Browser Pool**: Spawns and recycles pages/contexts in a single Chromium daemon.
5. **HTML Parser**: Resolves HTML structures into raw dictionaries.
6. **Normalization & Schema**: Normalizes formats (prices, ratings, currencies) and validates against domain definitions.
7. **Output Product**: Standardizes outputs into `Product` domain entities ready for ingestion or database upsert.

---

## 3. Components Built

### Amazon Collector & Parser
* **Responsibilities**: Health check verification, mobile phone listing discovery, and detail page parsing.
* **Workflow**: Navigates Amazon URLs, detects and extracts standard `/dp/{ASIN}` links, stores raw HTML, and extracts mobile features.
* **Parsing Strategy**: Selects product title blocks (`#productTitle`), filters brand fields, handles dynamic image map patterns, and scrapes technical product detail lists.
* **Error Handling**: Gracefully returns empty structures on missing selectors and maps unknown keys to fallback defaults.

### BestBuy Collector & Parser
* **Responsibilities**: Dell/HP laptop listing page crawls and spec mapping.
* **Workflow**: Crawls list directories, filters `/site/...` clean product targets, and normalizes laptop specs.
* **Parsing Strategy**: Locates brand strings (`.brand-link`), extracts REGEX-cleaned price items, and converts spec table data to typed attributes.
* **Differences from Amazon**: Amazon uses key-value lists (`#detailBullets_feature_div`) or detail tables (`prodDetTable`), while BestBuy uses standard specifications tables (`.specs-table`). BestBuy relies on numeric SKUs in URL patterns, whereas Amazon utilizes 10-character alphanumeric ASIN IDs.

### Browser Pool (`LayeredBrowserPool`)
* **Purpose**: Manages page allocations to prevent leaks and thread blocks.
* **Lifecycle**: Launches headless Chromium instances using `async_playwright()`. Closes context blocks and releases page resources inside structured `asynccontextmanager` hooks.
* **Resource Reuse**: Pools multiple pages per context block and context blocks per browser process to maximize throughput.

### Request Manager (`RequestManager`)
* **Retries & Timeouts**: Retries failed attempts up to `max_retries` using exponential backoff (\(factor \times 2^{retry}\)) coupled with randomized delay jitter to bypass cloud flares.
* **Header Rotation**: Rotates standard User-Agent headers across random request boundaries.
* **Rate Limiting**: Implements token-bucket rate limits (`RateLimiter`) to regulate operations.

### Parsing Pipeline
* **BeautifulSoup Parsing**: Instantiates BS4 processors using the standard `html.parser` parser.
* **Normalization**: Trims trailing whitespaces, cleans price strings into floats, maps currencies, and normalizes specifications tables keys to snake_case.
* **Validation**: Implements strict Pydantic v2 validation during mapping to `Product` model instances.

### Product Models
* **Product**: Root domain entity representing price, rating, reviews, availability, metadata, and specification details.
* **MobileSpecs & LaptopSpecs**: Sub-specs encapsulating domain-specific hardware parameters.
* **Enums**: Strongly typed category types (`CategoryEnum`), currency flags (`CurrencyEnum`), and priority levels (`PriorityEnum`).

---

## 4. Data Flow

The diagram below outlines the full lifecycle of processing a URL:

```
[Target URL Enqueued]
        │
        ▼
[Acquire Playwright Page from BrowserPool]
        │
        ▼
[Execute Goto via RequestManager (Header Rotator / Rate Limiter)]
        │
        ├──────────────────────────┐
        ▼ (Success)                ▼ (Failure)
[Save Raw HTML Content]     [Raise MaxRetriesExceededError]
        │                          │
        ▼                          ▼
[Initialize BS4 Parser]     [Mark URL as Failed in DB]
        │
        ▼
[Extract Core Fields (Title, Brand, Price)]
        │
        ▼
[Extract Specifications (Specs Table Parsing)]
        │
        ▼
[Run Normalizer Layer (Snake_Case Spec Keys, Float Conversion)]
        │
        ▼
[Validate Model via Pydantic Schema]
        │
        ▼
[Assess Quality Score via DQA Assessor]
        │
        ├──────────────────────────┐
        ▼ (Score >= 0.8)           ▼ (Score < 0.8)
[Save to PostgreSQL DB]     [Raise DataQualityError & Discard]
```

---

## 5. Folder Structure

```
ai_shopping_assistant/
│
├── src/
│   ├── collectors/              # Concrete site scraper implementations
│   │   ├── amazon.py            # Amazon mobile collector & parser
│   │   └── bestbuy.py           # BestBuy laptop collector & parser
│   │
│   ├── core/                    # System utilities and logging
│   │   ├── request_manager.py   # Rate limiting, backoff, and UA rotation
│   │   └── exceptions.py        # System exception declarations
│   │
│   ├── domain/                  # Pydantic schemas and domain enums
│   │   ├── models/              # Product and Spec schemas
│   │   └── enums.py             # Strongly typed Domain enums
│   │
│   ├── engine/                  # Processing orchestrators
│   │   ├── pipeline.py          # 8-stage scraping orchestrator
│   │   └── registry.py          # Dynamic plugin registrar
│   │
│   ├── infrastructure/          # Browser management and db storage
│   │   ├── browser/             # Layered browser context pools
│   │   └── db/                  # PostgreSQL model definitions
│   │
│   └── interfaces/              # Collector & Parser abstract class contracts
│       ├── collector.py         # CollectorInterface and BaseCollector
│       └── parser.py            # ParserInterface and BaseParser
│
└── tests/
    └── unit/                    # Test suites
        ├── test_scraping_runtime.py   # Scraper/Pipeline test suite
        └── test_collector_registry.py # Registrar validation tests
```

---

## 6. Design Decisions

### Clean Architecture
Decoupling raw scraping dependencies from pipeline logic allows the database storage engine, Playwright bindings, and target parsing rules to change independently.

### Repository Pattern
Hides database persistence mechanics behind interfaces (`ProductRepositoryInterface`), facilitating transition to NoSQL document stores in future cycles without modifying execution layers.

### Interfaces
Ensures a strict, contract-based plugin system (`BaseCollector`, `BaseParser`) that enables automated registration.

### Pydantic v2
Enforces runtime data constraints at boundary points and handles type serialization out-of-the-box.

### BeautifulSoup
Chosen for its stability, ease of HTML tree traversal, and low parsing footprint.

---

## 7. Code Quality

The codebase enforces strict checks to maintain production quality.

| Verification Tool | Status / Target | Purpose |
|---|---|---|
| **Ruff** | All Checks Passed | Ensures uniform formatting, checks loop conventions, and verifies code structure. |
| **MyPy** | Success (Strict Mode) | Verifies type hints, enforces generic typing, and prevents runtime type mismatches. |
| **Pytest** | 11 Tests Passed | Validates the pipeline end-to-end (Acquisition, DQA, Parsing, Deduplication). |

---

## 8. Testing Strategy

* **Unit Tests**: Asserts helper functionality (e.g. rate limiters, backoff math, string parsing rules) independently.
* **Parser Tests**: Exercises the parser against mock HTML fragments to assert attribute, image, and spec extraction.
* **Collector Tests**: Verifies health checks and link discovery behaviors without hitting live target endpoints.
* **Coverage**: Exercises the pipeline processing lifecycle, tracking database updates, duplicate checks, and storage fallbacks.

---

## 9. Challenges Faced & Resolved

### Dynamic HTML structures
* *Challenge*: Amazon frequently changes the location of the product reviews block.
* *Solution*: Broadened the selector pattern to check `#acrCustomerReviewText`, `#acrCustomerReviewLink`, and `.a-size-base`.

### Parser Key Mismatches
* *Challenge*: Spec table headers contain capitalization and symbols (e.g., `System Memory (RAM)`).
* *Solution*: Implemented key normalization to transform raw headers into clean snake_case identifiers, and added a multi-key lookup fallback (`_find_spec`) to resolve matches.

---

## 10. Lessons Learned

* **DQA Guardrails**: Enforcing strict DQA metrics ensures corrupt or partially parsed payloads are caught before database ingestion.
* **Refactoring for Ruff PLR0915**: Keeping statement counts under 50 by extracting modular helper methods significantly improves code legibility.

---

## 11. Production Readiness

Phase 2 meets production specifications by providing:
1. **Type Safety**: Avoids untyped generics, and uses `cast` statements to eliminate implicit `Any` mappings.
2. **Graceful Failures**: Resilient retries and connection timeouts prevent crawler blockages.
3. **Traceability**: Comprehensive structured logging records processing parameters for easy debugging.

---

## 12. Phase 2 Achievements

- [x] Layered Browser Pool (`LayeredBrowserPool`)
- [x] Request Manager with backoff jitter (`RequestManager`)
- [x] Amazon Mobile Collector plugin (`AmazonCollector`)
- [x] BestBuy Laptop Collector plugin (`BestBuyCollector`)
- [x] HTML Parsing & Spec Normalization (`BaseParser`)
- [x] Domain Model validation (`LaptopSpecs`, `MobileSpecs`)
- [x] Strict MyPy Compliance
- [x] Ruff Linting Clean
- [x] End-to-End Pytest Verification

---

## 13. Limitations (Future Work)

The following components are out of scope for Phase 2 and are deferred to later project cycles:
* **Distributed Queue**: Scale from in-memory processing to Redis-backed queues.
* **Cron Scheduling**: Execute crawling tasks on fixed crontab intervals.
* **Distributed Observability**: Export OTel spans to Jaeger/Collector instances.
* **Docker Packaging**: Containerize worker daemons for orchestrators like Kubernetes.

---

## 14. Phase 3 Preview

Phase 3 will scale the scraping runtime into a distributed orchestrator. It will implement background tasks, asynchronous scheduling, distributed queue management, and Postgres storage persistence.

---

## 15. Conclusion

Phase 2 builds a solid foundations for the scraping runtime. By combining modular parsing plugins, resilient Playwright execution, and strict schema validation, the platform is well-positioned for scaling into a high-performance distributed architecture.
