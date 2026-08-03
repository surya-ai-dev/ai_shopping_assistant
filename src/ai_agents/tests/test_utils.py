"""Unit tests verifying helper utility functions."""

import time

from src.ai_agents.utils.helpers import (
    clean_whitespace,
    estimate_token_count,
    sanitize_text,
)
from src.ai_agents.utils.ids import (
    generate_conversation_id,
    generate_request_id,
    generate_trace_id,
)
from src.ai_agents.utils.timer import Timer


def test_id_generators() -> None:
    """Verify prefixing and string length of trace identifiers."""
    req_id = generate_request_id()
    conv_id = generate_conversation_id()
    trace_id = generate_trace_id()

    assert req_id.startswith("req_")
    assert conv_id.startswith("conv_")
    assert len(trace_id) == 32


def test_timer_context_manager() -> None:
    """Verify that Timer context manager correctly tracks elapsed execution time."""
    with Timer() as timer:
        time.sleep(0.01)

    assert timer.elapsed_ms > 0.0
    assert timer.elapsed_ms < 100.0  # Safe upper margin for test latency runtime


def test_text_sanitization() -> None:
    """Verify that sanitize_text strips HTML tags and non-printable elements."""
    raw_text = "<script>alert('dangerous')</script> Hello \x00 World"
    sanitized = sanitize_text(raw_text)
    assert "script" not in sanitized
    assert "Hello" in sanitized
    assert "World" in sanitized


def test_clean_whitespace() -> None:
    """Verify clean_whitespace normalizes tabs, spaces, and duplicate runs."""
    dirty_text = "  Hello \t\t  to  \n the   world. "
    cleaned = clean_whitespace(dirty_text)
    assert cleaned == "Hello to the world."


def test_estimate_token_count() -> None:
    """Verify word-to-token count heuristics."""
    assert estimate_token_count("") == 0
    assert estimate_token_count("Hello world") == 2  # 2 * 1.3 = 2.6 -> 2
