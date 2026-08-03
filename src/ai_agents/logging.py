"""Custom structured logging adapter for the AI Agents platform."""

from typing import Any

from src.core.logging import get_logger


class AILogger:
    """Wrapper around structlog logger to ensure trace, request, and timing context.

    Ensures that every log message from the AI Agent system includes trace, correlation,
    and metadata IDs when available.
    """

    def __init__(
        self,
        component_name: str,
        request_id: str | None = None,
        conversation_id: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Initialize the AI Logger adapter.

        Args:
            component_name: Name of the AI component (e.g. Planner, Router).
            request_id: Unique HTTP request ID string.
            conversation_id: Unique chat conversation ID string.
            trace_id: OpenTelemetry trace correlation ID.
        """
        self._logger = get_logger(f"ai_agents.{component_name}")
        self._component_name = component_name
        self._context: dict[str, Any] = {
            "component_name": component_name,
        }
        if request_id:
            self._context["request_id"] = request_id
        if conversation_id:
            self._context["conversation_id"] = conversation_id
        if trace_id:
            self._context["trace_id"] = trace_id

    def bind(self, **kwargs: Any) -> "AILogger":
        """Bind new key-value context elements returning a new logger instance.

        Args:
            **kwargs: Metadatas to log in future calls.

        Returns:
            A new AILogger instance with updated context.
        """
        new_logger = AILogger(
            component_name=self._component_name,
            request_id=kwargs.get("request_id") or self._context.get("request_id"),
            conversation_id=kwargs.get("conversation_id") or self._context.get("conversation_id"),
            trace_id=kwargs.get("trace_id") or self._context.get("trace_id"),
        )
        # Copy other keys
        new_logger._context.update({k: v for k, v in self._context.items() if k not in ["request_id", "conversation_id", "trace_id"]})
        new_logger._context.update({k: v for k, v in kwargs.items() if k not in ["request_id", "conversation_id", "trace_id"]})
        return new_logger

    def _log(
        self,
        level: str,
        event: str,
        execution_time_ms: float | None = None,
        **kwargs: Any,
    ) -> None:
        """Centralized log routing method."""
        payload = {**self._context, **kwargs}
        if execution_time_ms is not None:
            payload["execution_time_ms"] = execution_time_ms

        log_func = getattr(self._logger, level, self._logger.info)
        log_func(event, **payload)

    def debug(self, event: str, execution_time_ms: float | None = None, **kwargs: Any) -> None:
        """Log a debug level message."""
        self._log("debug", event, execution_time_ms, **kwargs)

    def info(self, event: str, execution_time_ms: float | None = None, **kwargs: Any) -> None:
        """Log an info level message."""
        self._log("info", event, execution_time_ms, **kwargs)

    def warning(self, event: str, execution_time_ms: float | None = None, **kwargs: Any) -> None:
        """Log a warning level message."""
        self._log("warning", event, execution_time_ms, **kwargs)

    def error(self, event: str, execution_time_ms: float | None = None, **kwargs: Any) -> None:
        """Log an error level message."""
        self._log("error", event, execution_time_ms, **kwargs)

    def exception(self, event: str, execution_time_ms: float | None = None, **kwargs: Any) -> None:
        """Log an exception level message, including exc_info."""
        self._log("exception", event, execution_time_ms, **kwargs)


def get_ai_logger(component_name: str) -> AILogger:
    """Convenience factory function for instantiating AI loggers."""
    return AILogger(component_name=component_name)
