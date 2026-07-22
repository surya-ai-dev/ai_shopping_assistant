"""Unit tests for CrawlWorker, WorkerPool, and CrawlPipeline integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.enums import CategoryEnum, URLStatusEnum
from src.domain.models.product import Product
from src.domain.models.url import DiscoveredURL
from src.engine.pipeline import ScrapePipeline
from src.frontier.frontier import URLFrontier
from src.pipeline.crawl_pipeline import CrawlerSettings, CrawlPipeline
from src.repositories.url import InMemoryURLRepository
from src.workers.pool import WorkerPool
from src.workers.worker import CrawlWorker


@pytest.mark.asyncio
async def test_crawl_worker_and_hooks_execution() -> None:
    """Test CrawlWorker executes scraping lifecycle, updates statuses, and triggers hooks."""
    repo = InMemoryURLRepository()
    frontier = URLFrontier(url_repository=repo)

    # Setup mock pipeline
    mock_pipeline = MagicMock(spec=ScrapePipeline)
    mock_product = Product(
        site_id="bestbuy_us",
        url="https://www.bestbuy.com/site/dell/123.p",
        sku="123",
        title="Dell Laptop",
        brand="Dell",
        model_name="XPS 13",
        category=CategoryEnum.LAPTOP,
        current_price=999.99,
    )
    mock_pipeline.process_url = AsyncMock(return_value=mock_product)

    # Setup hooks tracking lists
    before_calls = []
    after_calls = []
    save_calls = []

    async def before_hook(url: str) -> None:
        before_calls.append(url)

    async def after_hook(url: str, html_size: int) -> None:
        after_calls.append((url, html_size))

    async def save_hook(prod: Product) -> None:
        save_calls.append(prod)

    # Instantiate worker
    worker = CrawlWorker(
        worker_id="worker_test",
        frontier=frontier,
        pipeline=mock_pipeline,
        before_request_hook=before_hook,
        after_request_hook=after_hook,
        on_save_hook=save_hook,
    )

    url_item = DiscoveredURL(
        url="https://www.bestbuy.com/site/dell/123.p",
        site_id="bestbuy_us",
        category=CategoryEnum.LAPTOP,
    )
    await frontier.add_url(url_item)

    # Execute a single worker processing run iteration
    # Since worker.run() runs in an infinite loop, we can test _process_item directly
    pulled_item = await frontier.get_next_url()
    await worker._process_item(pulled_item)

    # Verify status completed
    repo_item = await repo.get_by_id(pulled_item.id)
    assert repo_item is not None
    assert repo_item.status == URLStatusEnum.COMPLETED

    # Verify worker metrics
    assert worker.processed_count == 1
    assert worker.success_count == 1
    assert worker.fail_count == 0

    # Verify pipeline triggers and hook parameters
    mock_pipeline.process_url.assert_called_once_with(pulled_item, task_id="worker_test")
    assert before_calls == ["https://www.bestbuy.com/site/dell/123.p"]
    assert after_calls == [("https://www.bestbuy.com/site/dell/123.p", len("Dell Laptop"))]
    assert save_calls[0].sku == "123"


@pytest.mark.asyncio
async def test_worker_pool_metrics_and_graceful_shutdown() -> None:
    """Test WorkerPool starts concurrent workers, aggregates metrics, and handles graceful stop."""
    repo = InMemoryURLRepository()
    frontier = URLFrontier(url_repository=repo)
    mock_pipeline = MagicMock(spec=ScrapePipeline)

    pool = WorkerPool(
        num_workers=3,
        frontier=frontier,
        pipeline=mock_pipeline,
    )

    # Start pool
    pool.start()
    assert len(pool.workers) == 3
    assert pool._active is True

    # Simulate metrics on workers
    pool.workers[0].processed_count = 5
    pool.workers[0].success_count = 4
    pool.workers[0].fail_count = 1
    pool.workers[1].processed_count = 3
    pool.workers[1].success_count = 3

    # Aggregate metrics
    metrics = pool.get_metrics()
    assert metrics["processed"] == 8
    assert metrics["success"] == 7
    assert metrics["failed"] == 1
    assert metrics["retries"] == 0

    # Stop pool
    await pool.stop()
    assert len(pool.workers) == 0
    assert pool._active is False


@pytest.mark.asyncio
async def test_crawl_pipeline_end_to_end() -> None:
    """Test CrawlPipeline registers seed list, schedules runs, and resolves termination checks."""
    repo = InMemoryURLRepository()
    frontier = URLFrontier(url_repository=repo)
    mock_pipeline = MagicMock(spec=ScrapePipeline)

    # Mock process_url to succeed and update state
    async def mock_process(item: DiscoveredURL, task_id: str) -> Product:
        # Simulate worker processing
        return Product(
            site_id=item.site_id,
            url=item.url,
            sku="mock_sku",
            title="Mock Product Title",
            brand="Brand",
            model_name="Model",
            category=CategoryEnum.LAPTOP,
            current_price=10.0,
        )

    mock_pipeline.process_url = mock_process

    settings = CrawlerSettings(num_workers=2, check_interval=0.1, timeout_seconds=2.0)
    pipeline = CrawlPipeline(
        frontier=frontier,
        scrape_pipeline=mock_pipeline,
        settings=settings,
    )

    seed_urls = [
        DiscoveredURL(url="https://www.bestbuy.com/site/dell/1.p", site_id="bestbuy_us"),
        DiscoveredURL(url="https://www.bestbuy.com/site/dell/2.p", site_id="bestbuy_us"),
    ]

    # Run crawl pipeline
    metrics = await pipeline.run(seed_urls)
    assert metrics["success"] == 2
    assert metrics["failed"] == 0
