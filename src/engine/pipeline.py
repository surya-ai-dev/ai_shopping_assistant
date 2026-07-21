"""Complete 8-Stage Execution Pipeline for Web Scraping Platform."""

import time

from src.core.exceptions import DataQualityError
from src.core.logging import get_logger, set_correlation_context
from src.core.metrics import (
    DATA_QUALITY_SCORE,
    PAGES_SCRAPED_TOTAL,
    PRODUCTS_EXTRACTED_TOTAL,
    SCRAPE_DURATION_SECONDS,
)
from src.core.request_manager import RequestManager
from src.core.telemetry import trace_span
from src.domain.enums import URLStatusEnum
from src.domain.models.product import Product
from src.domain.models.url import DiscoveredURL
from src.engine.deduplication import DuplicateDetector
from src.engine.registry import CollectorRegistry
from src.infrastructure.browser.browser_pool import LayeredBrowserPool
from src.interfaces.raw_storage import RawHTMLStorageInterface
from src.interfaces.repository import DiscoveredURLRepositoryInterface, ProductRepositoryInterface
from src.quality.assessor import DataQualityAssessor

logger = get_logger(__name__)


class ScrapePipeline:
    """
        Multi-stage scraping pipeline:

        Collect
        → Raw Storage
        → Parse
        → Normalize
        → Validate
        → DQA
        → Deduplicate
        → Persistence.
        """
    def __init__(
        self,
        browser_pool: LayeredBrowserPool,
        raw_storage: RawHTMLStorageInterface,
        product_repo: ProductRepositoryInterface,
        url_repo: DiscoveredURLRepositoryInterface | None = None,
        request_manager: RequestManager | None = None,
        quality_assessor: DataQualityAssessor | None = None,
        duplicate_detector: DuplicateDetector | None = None,
    ) -> None:
        self.browser_pool = browser_pool
        self.raw_storage = raw_storage
        self.product_repo = product_repo
        self.url_repo = url_repo
        self.request_manager = request_manager or RequestManager()
        self.quality_assessor = quality_assessor or DataQualityAssessor()
        self.duplicate_detector = duplicate_detector or DuplicateDetector(repository=product_repo)

    async def process_url(self, item: DiscoveredURL, task_id: str = "task_0") -> Product | None:
        """Execute complete multi-stage pipeline for a single target DiscoveredURL item.

        Args:
            item: Target DiscoveredURL domain model.
            task_id: Active worker task correlation string.

        Returns:
            Saved Product domain model or None if processing failed.
        """
        set_correlation_context(site_id=item.site_id, task_id=task_id, run_id=item.job_id)
        start_time = time.monotonic()

        async with trace_span(
            "scrape_pipeline_process_url", attributes={"url": item.url, "site_id": item.site_id}
        ):
            try:
                # Stage 1: Collect Page (Playwright + RequestManager)
                collector_cls = CollectorRegistry.get_collector(item.site_id)
                collector = collector_cls(request_manager=self.request_manager)

                async with self.browser_pool.acquire_page() as page:
                    await collector.fetch_page(page, item.url)
                    html_content = await page.content()

                elapsed_seconds = time.monotonic() - start_time
                SCRAPE_DURATION_SECONDS.labels(collector_name=item.site_id).observe(elapsed_seconds)
                PAGES_SCRAPED_TOTAL.labels(collector_name=item.site_id, status="success").inc()

                # Stage 2: Store Raw HTML
                raw_payload_id = await self.raw_storage.save_raw_html(
                    url=item.url, site_id=item.site_id, html_content=html_content
                )

                # Stage 3 & 4: Parse & Normalize
                parser_cls = CollectorRegistry.get_parser(item.site_id)
                parser = parser_cls()
                product = await parser.parse(
                    html_content=html_content, url=item.url, raw_payload_id=raw_payload_id
                )

                # Stage 5: Validate Schema (Pydantic model validation implicitly executed on instantiate)

                # Stage 6: Data Quality Assessment (DQA)
                quality_report = self.quality_assessor.assess_product(product)
                DATA_QUALITY_SCORE.labels(category=product.category.value).observe(
                    quality_report.overall_quality_score
                )

                if not quality_report.is_passed:
                    logger.warning(
                        "Product failed data quality evaluation threshold",
                        url=item.url,
                        overall_score=quality_report.overall_quality_score,
                        missing=quality_report.missing_fields,
                        invalid=quality_report.invalid_fields,
                    )
                    raise DataQualityError(
                        f"Product failed quality score thresholds (Score: {quality_report.overall_quality_score})",
                        details={"report": quality_report.model_dump()},
                    )

                # Stage 7: Duplicate Detection
                is_dup, matched = await self.duplicate_detector.is_duplicate(product)
                if is_dup and matched:
                    logger.info("Product flagged as duplicate, merging price history", url=item.url)

                # Stage 8: Repository Persistence to PostgreSQL
                saved_product = await self.product_repo.upsert_product(product)
                PRODUCTS_EXTRACTED_TOTAL.labels(
                    category=product.category.value, collector_name=item.site_id
                ).inc()

                # Update URL Status in queue DB
                if self.url_repo and item.id:
                    await self.url_repo.update_status(item.id, URLStatusEnum.COMPLETED)

                logger.info(
                    "Pipeline successfully processed product",
                    product_id=saved_product.id,
                    title=saved_product.title,
                    price=saved_product.current_price,
                )
                return saved_product

            except Exception as exc:
                PAGES_SCRAPED_TOTAL.labels(collector_name=item.site_id, status="error").inc()
                logger.error("Pipeline failure during URL processing", url=item.url, error=str(exc))

                if self.url_repo and item.id:
                    await self.url_repo.update_status(
                        item.id, URLStatusEnum.FAILED, error_msg=str(exc)
                    )
                raise
