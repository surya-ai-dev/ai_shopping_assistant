"""Unit tests for URLFrontier and PriorityQueue."""

import pytest

from src.domain.enums import CategoryEnum, PriorityEnum, URLStatusEnum
from src.domain.models.url import DiscoveredURL
from src.frontier.frontier import URLFrontier
from src.frontier.queue import PriorityQueue
from src.repositories.url import InMemoryURLRepository


@pytest.mark.asyncio
async def test_priority_queue_duplicate_prevention_and_fifo() -> None:
    """Test duplicate prevention and priority/FIFO sorting of equal priority items."""
    pq = PriorityQueue()

    url_high = DiscoveredURL(
        url="https://www.amazon.com/dp/high",
        site_id="amazon_us",
        priority=PriorityEnum.HIGH,
    )
    url_med_1 = DiscoveredURL(
        url="https://www.amazon.com/dp/med1",
        site_id="amazon_us",
        priority=PriorityEnum.MEDIUM,
    )
    url_med_2 = DiscoveredURL(
        url="https://www.amazon.com/dp/med2",
        site_id="amazon_us",
        priority=PriorityEnum.MEDIUM,
    )
    url_low = DiscoveredURL(
        url="https://www.amazon.com/dp/low",
        site_id="amazon_us",
        priority=PriorityEnum.LOW,
    )

    # Put high and low
    await pq.put(url_med_1)
    await pq.put(url_high)
    await pq.put(url_low)

    # Attempt to put duplicate (should return False)
    is_queued = await pq.put(url_med_1)
    assert is_queued is False
    assert pq.qsize() == 3

    # Pull first (should be high priority)
    first = await pq.get()
    assert first.url == "https://www.amazon.com/dp/high"

    # Enqueue second medium item
    await pq.put(url_med_2)

    # Pull remaining (should be med1, then med2 (FIFO), then low)
    second = await pq.get()
    assert second.url == "https://www.amazon.com/dp/med1"

    third = await pq.get()
    assert third.url == "https://www.amazon.com/dp/med2"

    fourth = await pq.get()
    assert fourth.url == "https://www.amazon.com/dp/low"
    assert pq.empty() is True


@pytest.mark.asyncio
async def test_url_frontier_operations_and_retries() -> None:
    """Test URLFrontier preloading, processing marks, and retry policy boundaries."""
    repo = InMemoryURLRepository()
    frontier = URLFrontier(url_repository=repo)

    url_item = DiscoveredURL(
        url="https://www.amazon.com/dp/B0CSB45V1D",
        site_id="amazon_us",
        category=CategoryEnum.MOBILE,
        max_attempts=2,
    )

    # Add URL (should save to repo and queue)
    added = await frontier.add_url(url_item)
    assert added is True
    assert frontier.queue.qsize() == 1

    # Add duplicate (should ignore)
    added_dup = await frontier.add_url(url_item)
    assert added_dup is False

    # Pull and mark processing
    next_item = await frontier.get_next_url()
    assert next_item.url == url_item.url
    await frontier.mark_processing(next_item.id)

    # First retry attempt (should keep in queue)
    retry_1 = await frontier.retry_failed(next_item, error_msg="Transient Error")
    assert retry_1 is True
    assert frontier.queue.qsize() == 1

    # Pull and retry second time (exceeds max_attempts=2, should mark as failed and not enqueue)
    next_item_2 = await frontier.get_next_url()
    retry_2 = await frontier.retry_failed(next_item_2, error_msg="Fatal Error")
    assert retry_2 is False
    assert frontier.queue.empty() is True

    # Validate final repository state
    repo_item = await repo.get_by_id(next_item.id)
    assert repo_item is not None
    assert repo_item.status == URLStatusEnum.FAILED
    assert repo_item.attempts == 2
    assert repo_item.last_error == "Fatal Error"
