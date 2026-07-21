"""Prometheus metrics collector definitions and server exporter initialization."""

from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Scraping & Request Metrics
PAGES_SCRAPED_TOTAL = Counter(
    "scraper_pages_scraped_total",
    "Total number of web pages fetched",
    ["collector_name", "status"],
)

SCRAPE_DURATION_SECONDS = Histogram(
    "scraper_scrape_duration_seconds",
    "Duration of page fetch and render operations in seconds",
    ["collector_name"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

REQUEST_RETRIES_TOTAL = Counter(
    "scraper_request_retries_total",
    "Total number of request retry attempts",
    ["collector_name", "reason"],
)

# Pipeline & Data Quality Metrics
PRODUCTS_EXTRACTED_TOTAL = Counter(
    "scraper_products_extracted_total",
    "Total extracted and parsed product listings",
    ["category", "collector_name"],
)

DATA_QUALITY_SCORE = Histogram(
    "scraper_data_quality_score",
    "Distribution of overall data quality assessment scores",
    ["category"],
    buckets=[0.5, 0.7, 0.8, 0.9, 0.95, 1.0],
)

DUPLICATE_PRODUCTS_TOTAL = Counter(
    "scraper_duplicate_products_total",
    "Total duplicate products detected during deduplication stage",
    ["category"],
)

# Queue & Worker Metrics
ACTIVE_WORKERS_GAUGE = Gauge(
    "scraper_active_workers",
    "Current number of active worker tasks executing pipelines",
)

QUEUE_DEPTH_GAUGE = Gauge(
    "scraper_url_queue_depth",
    "Current number of pending URLs in the AsyncURLQueue",
    ["priority"],
)

ERRORS_TOTAL = Counter(
    "scraper_errors_total",
    "Total application exceptions encountered",
    ["error_type", "component"],
)


def start_metrics_server(port: int = 8000) -> None:
    """Start Prometheus HTTP metrics endpoint server."""
    start_http_server(port)
