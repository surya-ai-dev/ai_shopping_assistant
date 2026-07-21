"""Unit tests for the scraping runtime components including Collectors, Parsers, BrowserPool, and RequestManager."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import Page, Response

from src.collectors.amazon import AmazonCollector, AmazonParser
from src.collectors.bestbuy import BestBuyCollector, BestBuyParser
from src.core.exceptions import MaxRetriesExceededError
from src.core.request_manager import RequestConfig, RequestManager
from src.domain.enums import CategoryEnum, CurrencyEnum
from src.domain.models.product import Product
from src.domain.models.url import DiscoveredURL
from src.engine.pipeline import ScrapePipeline
from src.engine.registry import CollectorRegistry
from src.infrastructure.browser.browser_pool import LayeredBrowserPool
from src.interfaces.raw_storage import RawHTMLStorageInterface
from src.interfaces.repository import DiscoveredURLRepositoryInterface, ProductRepositoryInterface


@pytest.mark.asyncio
async def test_request_config_and_manager() -> None:
    """Test RequestConfig customization and RequestManager initialization and delay/UA rotation."""
    config = RequestConfig(
        rate_per_minute=60,
        max_retries=2,
        backoff_factor=1.5,
        min_delay_ms=10,
        max_delay_ms=20,
    )
    manager = RequestManager(config=config)

    assert manager.max_retries == 2
    assert manager.backoff_factor == 1.5
    assert manager.min_delay_ms == 10
    assert manager.max_delay_ms == 20

    ua = manager.get_random_user_agent()
    assert isinstance(ua, str)
    assert len(ua) > 0

    # Test delay executing successfully without blocking for long
    await manager.apply_random_delay()


@pytest.mark.asyncio
async def test_request_manager_retries_and_failure() -> None:
    """Test that RequestManager retries on failure and eventually raises MaxRetriesExceededError."""
    manager = RequestManager(
        max_retries=2,
        min_delay_ms=1,
        max_delay_ms=2,
        jitter_ms=1,
    )

    mock_page = MagicMock(spec=Page)
    mock_page.set_extra_http_headers = AsyncMock()
    # Mock goto raising an exception
    mock_page.goto = AsyncMock(side_effect=Exception("Connection refused"))

    with pytest.raises(MaxRetriesExceededError) as exc_info:
        await manager.execute_goto(mock_page, "https://example.com/fail")

    assert "Failed to navigate to" in str(exc_info.value)
    assert mock_page.goto.call_count == 2


@pytest.mark.asyncio
async def test_browser_pool_lifecycle() -> None:
    """Test LayeredBrowserPool lifecycle initialization, acquisition, and shutdown via mock."""
    pool = LayeredBrowserPool(
        headless=True,
        max_browsers=1,
        max_contexts_per_browser=1,
        max_pages_per_context=1,
    )

    mock_page = MagicMock(spec=Page)
    mock_page.is_closed = MagicMock(return_value=False)
    mock_page.close = AsyncMock()

    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_context.close = AsyncMock()

    mock_browser = MagicMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_chromium = MagicMock()
    mock_chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright = MagicMock()
    mock_playwright.chromium = mock_chromium
    mock_playwright.stop = AsyncMock()

    with patch(
        "src.infrastructure.browser.browser_pool.async_playwright"
    ) as mock_async_playwright:
        # Create an async mock context manager
        async_playwright_ctx = AsyncMock()
        async_playwright_ctx.start = AsyncMock(return_value=mock_playwright)
        mock_async_playwright.return_value = async_playwright_ctx

        await pool.initialize()
        assert pool._initialized is True

        async with pool.acquire_page() as page:
            assert page == mock_page

        mock_context.new_page.assert_called_once()

        await pool.close()
        assert pool._initialized is False
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()


@pytest.mark.asyncio
async def test_bestbuy_parser_extraction() -> None:
    """Test BestBuyParser correctly parses raw product HTML and normalizes/validates data."""
    html_content = """
    <html>
        <body>
            <h1 class="sku-title">Dell XPS 15 Laptop - Intel Core i7 - 16GB - 512GB SSD</h1>
            <div class="brand-link">Dell</div>
            <div class="priceView-customer-price">
                <span>$1,499.99</span>
            </div>
            <div class="priceView-pricing-regular-price">
                <span>$1,799.99</span>
            </div>
            <span class="sku-value" data-sku="6537350">6537350</span>
            <div class="model-number">XPS9530-7581SLV-PUS</div>
            <img class="primary-image" src="https://images.bestbuy.com/xps15.jpg" />
            <button class="add-to-cart-button">Add to Cart</button>
            <div class="c-ratings-reviews">4.5 out of 5 stars</div>
            <div class="c-reviews">(120 Reviews)</div>
            <table class="specs-table">
                <tr class="specs-table-row">
                    <td class="spec-label">Processor Model</td>
                    <td class="spec-value">Intel Core i7-13700H</td>
                </tr>
                <tr class="specs-table-row">
                    <td class="spec-label">System Memory (RAM)</td>
                    <td class="spec-value">16 gigabytes</td>
                </tr>
                <tr class="specs-table-row">
                    <td class="spec-label">Total Storage Capacity</td>
                    <td class="spec-value">512 gigabytes</td>
                </tr>
                <tr class="specs-table-row">
                    <td class="spec-label">Screen Size</td>
                    <td class="spec-value">15.6 inches</td>
                </tr>
                <tr class="specs-table-row">
                    <td class="spec-label">Operating System</td>
                    <td class="spec-value">Windows 11 Home</td>
                </tr>
            </table>
        </body>
    </html>
    """

    parser = BestBuyParser()
    product = await parser.parse(
        html_content, "https://www.bestbuy.com/site/dell-xps-15/6537350.p"
    )

    assert isinstance(product, Product)
    assert product.title == "Dell XPS 15 Laptop - Intel Core i7 - 16GB - 512GB SSD"
    assert product.brand == "Dell"
    assert product.current_price == 1499.99
    assert product.original_price == 1799.99
    assert product.currency == CurrencyEnum.USD
    assert product.sku == "6537350"
    assert product.model_name == "XPS9530-7581SLV-PUS"
    assert product.is_in_stock is True
    assert product.rating == 4.5
    assert product.review_count == 120
    assert product.image_urls == ["https://images.bestbuy.com/xps15.jpg"]

    # Verify laptop specific specs
    assert product.specs.processor == "Intel Core i7-13700H"
    assert product.specs.ram_gb == 16
    assert product.specs.storage_gb == 512
    assert product.specs.screen_size_inches == 15.6
    assert product.specs.operating_system == "Windows 11 Home"


@pytest.mark.asyncio
async def test_amazon_parser_extraction() -> None:
    """Test AmazonParser correctly parses raw product HTML and normalizes/validates data."""
    html_content = """
    <html>
        <body>
            <span id="productTitle">Samsung Galaxy S24 Ultra, 512GB, Titanium Black</span>
            <div id="bylineInfo">Brand: Samsung</div>
            <span class="a-price">
                <span class="a-offscreen">$1,299.99</span>
            </span>
            <span class="basisPrice">
                <span class="a-offscreen">$1,419.99</span>
            </span>
            <img id="landingImage" src="https://media-amazon.com/images/s24.jpg" />
            <div id="availability">In Stock</div>
            <span class="a-icon-alt">4.7 out of 5 stars</span>
            <span id="acrCustomerReviewText">4,250 ratings</span>
            <table class="prodDetTable">
                <tr><th>OS</th><td>Android 14</td></tr>
                <tr><th>RAM</th><td>12 GB</td></tr>
                <tr><th>Storage</th><td>512 GB</td></tr>
                <tr><th>Screen Size</th><td>6.8 inches</td></tr>
                <tr><th>Battery Capacity</th><td>5000 mAh</td></tr>
            </table>
        </body>
    </html>
    """

    parser = AmazonParser()
    product = await parser.parse(
        html_content, "https://www.amazon.com/dp/B0CSB45V1D"
    )

    assert isinstance(product, Product)
    assert product.title == "Samsung Galaxy S24 Ultra, 512GB, Titanium Black"
    assert product.brand == "Samsung"
    assert product.current_price == 1299.99
    assert product.original_price == 1419.99
    assert product.currency == CurrencyEnum.USD
    assert product.sku == "B0CSB45V1D"
    assert product.is_in_stock is True
    assert product.rating == 4.7
    assert product.review_count == 4250
    assert product.image_urls == ["https://media-amazon.com/images/s24.jpg"]

    # Verify mobile specific specs
    assert product.specs.ram_gb == 12
    assert product.specs.storage_gb == 512
    assert product.specs.screen_size_inches == 6.8
    assert product.specs.battery_capacity_mah == 5000
    assert product.specs.operating_system == "Android 14"


@pytest.mark.asyncio
async def test_scrape_pipeline_execution() -> None:
    """Test that the ScrapePipeline runs each stage from acquisition to repository persistence."""
    mock_browser_pool = MagicMock(spec=LayeredBrowserPool)
    mock_page = MagicMock(spec=Page)
    mock_page.content = AsyncMock(
        return_value="""
    <html>
        <body>
            <h1 class="sku-title">Dell XPS 15 Laptop - Intel Core i7 - 16GB - 512GB SSD</h1>
            <div class="brand-link">Dell</div>
            <div class="priceView-customer-price">
                <span>$1,499.99</span>
            </div>
            <div class="priceView-pricing-regular-price">
                <span>$1,799.99</span>
            </div>
            <span class="sku-value" data-sku="6537350">6537350</span>
            <div class="model-number">XPS9530-7581SLV-PUS</div>
            <img class="primary-image" src="https://images.bestbuy.com/xps15.jpg" />
            <button class="add-to-cart-button">Add to Cart</button>
            <div class="c-ratings-reviews">4.5 out of 5 stars</div>
            <div class="c-reviews">(120 Reviews)</div>
            <table class="specs-table">
                <tr class="specs-table-row">
                    <td class="spec-label">Processor Model</td>
                    <td class="spec-value">Intel Core i7-13700H</td>
                </tr>
                <tr class="specs-table-row">
                    <td class="spec-label">System Memory (RAM)</td>
                    <td class="spec-value">16 gigabytes</td>
                </tr>
                <tr class="specs-table-row">
                    <td class="spec-label">Total Storage Capacity</td>
                    <td class="spec-value">512 gigabytes</td>
                </tr>
                <tr class="specs-table-row">
                    <td class="spec-label">Screen Size</td>
                    <td class="spec-value">15.6 inches</td>
                </tr>
                <tr class="specs-table-row">
                    <td class="spec-label">Operating System</td>
                    <td class="spec-value">Windows 11 Home</td>
                </tr>
            </table>
        </body>
    </html>
        """
    )

    @asynccontextmanager
    async def mock_acquire_page(
        timeout: float = 30.0,
    ) -> AsyncGenerator[Page, None]:
        yield mock_page

    mock_browser_pool.acquire_page = mock_acquire_page

    mock_raw_storage = MagicMock(spec=RawHTMLStorageInterface)
    mock_raw_storage.save_raw_html = AsyncMock(return_value="payload_hash_123")

    mock_product_repo = MagicMock(spec=ProductRepositoryInterface)
    mock_product_repo.upsert_product = AsyncMock(
        side_effect=lambda p: p
    )  # return the product mock back

    mock_url_repo = MagicMock(spec=DiscoveredURLRepositoryInterface)
    mock_url_repo.update_status = AsyncMock(return_value=True)

    class MockBestBuyCollector(BestBuyCollector):
        async def fetch_page(self, page: Page, url: str) -> Response | None:
            pass

    mock_fetch_page = AsyncMock()
    # Pre-register bestbuy_us collector in the test suite
    CollectorRegistry.register("bestbuy_us", MockBestBuyCollector, BestBuyParser)

    pipeline = ScrapePipeline(
        browser_pool=mock_browser_pool,
        raw_storage=mock_raw_storage,
        product_repo=mock_product_repo,
        url_repo=mock_url_repo,
    )

    url_item = DiscoveredURL(
        id="url_uuid_456",
        url="https://www.bestbuy.com/site/dell-xps-15/6537350.p",
        site_id="bestbuy_us",
        category=CategoryEnum.LAPTOP,
    )

    # Process the URL through the pipeline
    with patch.object(MockBestBuyCollector, "fetch_page", mock_fetch_page):
        product = await pipeline.process_url(url_item)

    assert product is not None
    assert product.title == "Dell XPS 15 Laptop - Intel Core i7 - 16GB - 512GB SSD"
    assert product.raw_payload_id == "payload_hash_123"

    mock_fetch_page.assert_called_once_with(
        mock_page, "https://www.bestbuy.com/site/dell-xps-15/6537350.p"
    )
    mock_raw_storage.save_raw_html.assert_called_once()
    mock_product_repo.upsert_product.assert_called_once()
    mock_url_repo.update_status.assert_called_once_with("url_uuid_456", "completed")


@pytest.mark.asyncio
async def test_collector_discover_urls_deduplication() -> None:
    """Test that BestBuyCollector and AmazonCollector deduplicate listing links during discovery."""
    mock_page = MagicMock(spec=Page)
    mock_page.content = AsyncMock(
        return_value="""
        <html>
            <body>
                <a href="/site/dell-xps-15/6537350.p">Dell XPS</a>
                <a href="/site/dell-xps-15/6537350.p">Dell XPS image link</a>
                <a href="/dp/B0CSB45V1D">Samsung Galaxy</a>
                <a href="/dp/B0CSB45V1D">Samsung Galaxy image link</a>
            </body>
        </html>
        """
    )
    mock_response = MagicMock(spec=Response)
    mock_response.status = 200

    mock_request_manager = MagicMock(spec=RequestManager)
    mock_request_manager.execute_goto = AsyncMock(return_value=mock_response)

    bb_collector = BestBuyCollector(request_manager=mock_request_manager)
    bb_urls = await bb_collector.discover_urls(
        mock_page, "https://www.bestbuy.com/laptops"
    )
    assert len(bb_urls) == 1
    assert bb_urls[0].url == "https://www.bestbuy.com/site/dell-xps-15/6537350.p"

    am_collector = AmazonCollector(request_manager=mock_request_manager)
    am_urls = await am_collector.discover_urls(
        mock_page, "https://www.amazon.com/phones"
    )
    assert len(am_urls) == 1
    assert am_urls[0].url == "https://www.amazon.com/dp/B0CSB45V1D"
