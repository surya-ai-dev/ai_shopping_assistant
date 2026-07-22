"""Pagination utilities for slicing list results and calculating page metadata."""

import math


class Page[T]:
    """Container holding a sliced subset of results and calculated pagination metadata."""

    def __init__(
        self,
        items: list[T],
        page: int,
        page_size: int,
        total_results: int,
    ) -> None:
        """Initialize the paginated page wrapper.

        Args:
            items: Slice of items representing the current page.
            page: Current page index (1-indexed).
            page_size: Page size limit.
            total_results: Total matching records count before slicing.
        """
        self.items = items
        self.page = page
        self.page_size = page_size
        self.total_results = total_results
        self.total_pages = math.ceil(total_results / page_size) if total_results > 0 else 0
        self.has_next = page < self.total_pages
        self.has_previous = page > 1


def paginate_list[T](items: list[T], page: int, page_size: int) -> Page[T]:
    """Slice a full result list based on page index and page size parameters.

    Args:
        items: The full list of results.
        page: Target page number index (1-indexed).
        page_size: Number of items per page.

    Returns:
        Page container containing the sliced sub-list and calculated metadata.
    """
    total_results = len(items)
    if total_results == 0:
        return Page(items=[], page=page, page_size=page_size, total_results=0)

    # Ensure page is at least 1
    safe_page = max(1, page)
    start_idx = (safe_page - 1) * page_size
    end_idx = start_idx + page_size
    sliced_items = items[start_idx:end_idx]

    return Page(
        items=sliced_items,
        page=safe_page,
        page_size=page_size,
        total_results=total_results,
    )
