"""OpenTelemetry tracing setup and span context management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode, Tracer


@lru_cache
def setup_telemetry(service_name: str = "ai-shopping-scraper", enabled: bool = True) -> None:
    """Initialize OpenTelemetry tracer provider.

    Args:
        service_name: Service identifier string.
        enabled: Toggle tracing initialization.
    """
    if not enabled:
        return

    resource = Resource.create(attributes={"service.name": service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)


def get_tracer(name: str = "src.scraper") -> Tracer:
    """Retrieve an OpenTelemetry tracer instance."""
    return trace.get_tracer(name)


@asynccontextmanager
async def trace_span(
    name: str, attributes: dict[str, Any] | None = None
) -> AsyncGenerator[trace.Span, None]:
    """Async context manager wrapper for creating traced OpenTelemetry spans.

    Args:
        name: Name of the span context.
        attributes: Key-value metadata dictionary to attach to span.
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, val in attributes.items():
                if val is not None:
                    span.set_attribute(key, str(val))
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
