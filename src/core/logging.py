"""Structured logging framework powered by structlog with correlation ID context."""
import logging
import sys
from functools import lru_cache
from typing import Any, cast

import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars


@lru_cache
def setup_logging(environment: str = "development", log_level: str = "INFO") -> None:
    """Initialize structured logging using structlog.

    Args:
        environment: Execution environment ('development' or 'production').
        log_level: Standard logging level string (DEBUG, INFO, WARNING, ERROR).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Standard python logging config
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if environment.lower() == "production":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(level)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a context-bound structlog logger instance."""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))


def set_correlation_context(
    run_id: str | None = None,
    trace_id: str | None = None,
    task_id: str | None = None,
    site_id: str | None = None,
    **kwargs: Any,
) -> None:
    """Bind correlation IDs to the async context variables for trace tracking."""
    context = {}
    if run_id:
        context["run_id"] = run_id
    if trace_id:
        context["trace_id"] = trace_id
    if task_id:
        context["task_id"] = task_id
    if site_id:
        context["site_id"] = site_id
    context.update(kwargs)
    bind_contextvars(**context)


def clear_correlation_context() -> None:
    """Clear all bound context variables."""
    clear_contextvars()
