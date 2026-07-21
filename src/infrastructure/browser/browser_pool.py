"""3-Tier Layered Playwright Resource Pool Architecture: BrowserPool -> ContextPool -> PagePool."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from src.core.exceptions import ResourceExhaustedError
from src.core.logging import get_logger

logger = get_logger(__name__)


class LayeredBrowserPool:
    """3-Tier layered resource pool managing Playwright Browser, Context, and Page lifecycles.

    Tier 1: Browser Pool - Manages high-level Chromium process instances.
    Tier 2: Context Pool - Manages isolated browser contexts (cookies, proxies, headers).
    Tier 3: Page Pool - Manages tab instances for parallel request processing.
    """

    def __init__(
        self,
        headless: bool = True,
        max_browsers: int = 3,
        max_contexts_per_browser: int = 5,
        max_pages_per_context: int = 10,
    ) -> None:
        self.headless = headless
        self.max_browsers = max_browsers
        self.max_contexts_per_browser = max_contexts_per_browser
        self.max_pages_per_context = max_pages_per_context

        self._playwright: Playwright | None = None
        self._browsers: list[Browser] = []
        self._contexts: list[BrowserContext] = []
        self._page_semaphore = asyncio.Semaphore(
            max_browsers * max_contexts_per_browser * max_pages_per_context
        )
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """Launch Playwright instance and spawn root browser instances."""
        async with self._lock:
            if self._initialized:
                return

            logger.info("Initializing Layered Browser Pool", max_browsers=self.max_browsers)
            self._playwright = await async_playwright().start()

            for _ in range(self.max_browsers):
                browser = await self._playwright.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-gpu",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                self._browsers.append(browser)

                # Initialize context pool for browser
                for _ in range(self.max_contexts_per_browser):
                    context = await browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent=(
                                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                                        "Chrome/125.0.0.0 Safari/537.36"
                                    ),
                        java_script_enabled=True,
                    )
                    self._contexts.append(context)

            self._initialized = True
            logger.info(
                "Browser pool initialized successfully",
                total_browsers=len(self._browsers),
                total_contexts=len(self._contexts),
            )

    @asynccontextmanager
    async def acquire_page(self, timeout: float = 30.0) -> AsyncGenerator[Page, None]:
        """Acquire an active Page tab from the context pool.

        Args:
            timeout: Maximum wait time in seconds to acquire page capacity semaphore.

        Yields:
            Active Playwright Page instance.
        """
        if not self._initialized:
            await self.initialize()

        try:
            await asyncio.wait_for(self._page_semaphore.acquire(), timeout=timeout)
        except TimeoutError as exc:
            raise ResourceExhaustedError(
                "Timed out waiting for available page in browser pool",
                details={"timeout": timeout},
            ) from exc

        # Select round-robin context
        context = self._contexts[hash(asyncio.current_task()) % len(self._contexts)]
        page: Page | None = None

        try:
            page = await context.new_page()
            yield page
        finally:
            if page and not page.is_closed():
                try:
                    await page.close()
                except Exception as exc:
                    logger.warning("Error closing page instance", error=str(exc))
            self._page_semaphore.release()

    async def close(self) -> None:
        """Gracefully close all open browser contexts, browser instances, and Playwright process."""
        async with self._lock:
            if not self._initialized:
                return

            logger.info("Shutting down Layered Browser Pool")
            for context in self._contexts:
                try:
                    await context.close()
                except Exception as exc:
                    logger.warning("Error closing browser context", error=str(exc))

            for browser in self._browsers:
                try:
                    await browser.close()
                except Exception as exc:
                    logger.warning("Error closing browser instance", error=str(exc))

            if self._playwright:
                await self._playwright.stop()

            self._browsers.clear()
            self._contexts.clear()
            self._initialized = False
            logger.info("Browser Pool shutdown complete")
