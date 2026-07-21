"""Request Manager providing rate limiting, retries with jitter, timeouts, and UA rotation."""

import asyncio
import random
import time
from dataclasses import dataclass, field

from playwright.async_api import Page, Response

from src.core.exceptions import MaxRetriesExceededError, RateLimitError
from src.core.logging import get_logger
from src.core.metrics import REQUEST_RETRIES_TOTAL

logger = get_logger(__name__)

# Production-grade User-Agent pool for browser header rotation
DEFAULT_USER_AGENTS = [
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
]

@dataclass
class RequestConfig:
    """Configuration options for RequestManager rate limits, retries, delays, and headers."""

    rate_per_minute: int = 30
    max_retries: int = 3
    backoff_factor: float = 2.0
    jitter_ms: int = 500
    min_delay_ms: int = 1000
    max_delay_ms: int = 3000
    user_agents: list[str] = field(default_factory=lambda: list(DEFAULT_USER_AGENTS))


class RateLimiter:
    """Async Token Bucket Rate Limiter."""

    def __init__(self, rate_per_minute: int = 30) -> None:
        self.rate_per_minute = rate_per_minute
        self.capacity = float(rate_per_minute)
        self.tokens = float(rate_per_minute)
        self.fill_rate = rate_per_minute / 60.0  # tokens per second
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token from the bucket, pausing if bucket is depleted."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.updated_at
            self.tokens = min(self.capacity, self.tokens + elapsed * self.fill_rate)
            self.updated_at = now

            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / self.fill_rate
                logger.debug("Rate limit active, delaying request", wait_time_seconds=wait_time)
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
                self.updated_at = time.monotonic()
            else:
                self.tokens -= 1.0


# HTTP Status Code Constants
HTTP_BAD_REQUEST = 400
HTTP_TOO_MANY_REQUESTS = 429
HTTP_SERVER_ERROR = 500


class RequestManager:
    """Manages page requests with rate limiting, exponential backoff retries, jitter, and UA rotation."""

    def __init__(
        self,
        rate_per_minute: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        jitter_ms: int = 500,
        min_delay_ms: int = 1000,
        max_delay_ms: int = 3000,
        user_agents: list[str] | None = None,
        config: RequestConfig | None = None,
    ) -> None:
        cfg = config or RequestConfig(
            rate_per_minute=rate_per_minute,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
            jitter_ms=jitter_ms,
            min_delay_ms=min_delay_ms,
            max_delay_ms=max_delay_ms,
            user_agents=user_agents or list(DEFAULT_USER_AGENTS),
        )
        self.rate_limiter = RateLimiter(cfg.rate_per_minute)
        self.max_retries = cfg.max_retries
        self.backoff_factor = cfg.backoff_factor
        self.jitter_ms = cfg.jitter_ms
        self.min_delay_ms = cfg.min_delay_ms
        self.max_delay_ms = cfg.max_delay_ms
        self.user_agents = cfg.user_agents

    def get_random_user_agent(self) -> str:
        """Get a random User-Agent string from pool."""
        return random.choice(self.user_agents)

    async def apply_random_delay(self) -> None:
        """Apply random delay to mimic human behavior and evade rate limits."""
        delay_seconds = random.uniform(self.min_delay_ms / 1000.0, self.max_delay_ms / 1000.0)
        await asyncio.sleep(delay_seconds)

    async def execute_goto(
        self,
        page: Page,
        url: str,
        timeout_ms: int = 30000,
        wait_until: str = "domcontentloaded",
        collector_name: str = "unknown",
    ) -> Response | None:
        """Execute Playwright page navigation with rate limiting and retry logic.

        Args:
            page: Active Playwright Page instance.
            url: Target URL to navigate to.
            timeout_ms: Maximum navigation timeout in milliseconds.
            wait_until: Navigation event condition ('load', 'domcontentloaded', 'networkidle').
            collector_name: Name of the active collector for metrics.

        Returns:
            Playwright Response object or None.
        """
        last_exception: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            await self.rate_limiter.acquire()
            await self.apply_random_delay()

            try:
                # Set extra HTTP headers with rotated User-Agent
                await page.set_extra_http_headers({"User-Agent": self.get_random_user_agent()})

                logger.debug(
                    "Executing page navigation",
                    url=url,
                    attempt=attempt,
                    max_retries=self.max_retries,
                )

                response = await page.goto(
                    url,
                    timeout=timeout_ms,
                    wait_until=wait_until,  # type: ignore
                )

                if response and response.status >= HTTP_BAD_REQUEST:
                    status = response.status
                    if status == HTTP_TOO_MANY_REQUESTS:
                        REQUEST_RETRIES_TOTAL.labels(
                            collector_name=collector_name, reason="rate_limited"
                        ).inc()
                        raise RateLimitError(f"HTTP 429 Rate Limited from {url}")
                    elif status >= HTTP_SERVER_ERROR:
                        REQUEST_RETRIES_TOTAL.labels(
                            collector_name=collector_name, reason="server_error"
                        ).inc()
                        logger.warning(
                            "Server returned error code", status=status, url=url, attempt=attempt
                        )

                return response

            except (TimeoutError, RateLimitError, Exception) as exc:
                last_exception = exc
                if isinstance(exc, asyncio.TimeoutError):
                    REQUEST_RETRIES_TOTAL.labels(
                        collector_name=collector_name, reason="timeout"
                    ).inc()
                    logger.warning("Navigation timed out", url=url, attempt=attempt)

                if attempt == self.max_retries:
                    break

                # Exponential backoff with random jitter
                backoff_base = self.backoff_factor ** (attempt - 1)
                jitter = random.uniform(0, self.jitter_ms / 1000.0)
                sleep_duration = backoff_base + jitter

                logger.info(
                    "Retrying navigation after failure",
                    url=url,
                    attempt=attempt,
                    sleep_duration_seconds=round(sleep_duration, 2),
                    error=str(exc),
                )
                await asyncio.sleep(sleep_duration)

        raise MaxRetriesExceededError(
            f"Failed to navigate to {url} after {self.max_retries} attempts",
            details={"url": url, "last_error": str(last_exception)},
        ) from last_exception
