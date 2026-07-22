"""Unit tests for search pagination utilities."""

from src.search.pagination import paginate_list


def test_paginate_list_basic() -> None:
    """Test pagination slices arrays and populates page index/has_next properties correctly."""
    items = [1, 2, 3, 4, 5]

    # First page
    page_1 = paginate_list(items, page=1, page_size=2)
    assert page_1.items == [1, 2]
    assert page_1.page == 1
    assert page_1.page_size == 2
    assert page_1.total_results == 5
    assert page_1.total_pages == 3
    assert page_1.has_next is True
    assert page_1.has_previous is False

    # Second page
    page_2 = paginate_list(items, page=2, page_size=2)
    assert page_2.items == [3, 4]
    assert page_2.has_next is True
    assert page_2.has_previous is True

    # Last page
    page_3 = paginate_list(items, page=3, page_size=2)
    assert page_3.items == [5]
    assert page_3.has_next is False
    assert page_3.has_previous is True


def test_paginate_list_empty_and_out_of_bounds() -> None:
    """Test pagination handles empty arrays and out-of-bounds parameters gracefully."""
    # Empty list
    page_empty = paginate_list([], page=1, page_size=10)
    assert page_empty.items == []
    assert page_empty.total_results == 0
    assert page_empty.total_pages == 0
    assert page_empty.has_next is False
    assert page_empty.has_previous is False

    # Out of bounds page index (should normalize index to 1)
    page_out_bounds = paginate_list([1, 2], page=-5, page_size=10)
    assert page_out_bounds.page == 1
    assert page_out_bounds.items == [1, 2]
