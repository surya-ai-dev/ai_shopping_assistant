"""OpenTelemetry tracing helpers for the AI Agents platform."""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from opentelemetry import trace

F = TypeVar("F", bound=Callable[..., Any])
tracer = trace.get_tracer("ai_agents")


def trace_span(span_name: str) -> Callable[[F], F]:
    """Decorator to wrap synchronous or asynchronous functions with an OpenTelemetry trace span.

    Args:
        span_name: Name of the trace span.

    Returns:
        Decorated function.
    """
    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("ai.component", span_name)
                    return await func(*args, **kwargs)
            return cast(F, async_wrapper)
        else:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with tracer.start_as_current_span(span_name) as span:
                    span.set_attribute("ai.component", span_name)
                    return func(*args, **kwargs)
            return cast(F, sync_wrapper)
    return decorator
