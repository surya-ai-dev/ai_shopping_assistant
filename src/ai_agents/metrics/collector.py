"""Prometheus metrics collector for the AI Agent platform."""

from prometheus_client import Counter, Histogram

# Histograms for recording component latency
AI_LATENCY_SECONDS = Histogram(
    "ai_component_latency_seconds",
    "Latency of AI platform components in seconds",
    ["component_name"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)

# Counter for tracking LLM token consumption by provider and model
AI_TOKEN_CONSUMPTION_TOTAL = Counter(
    "ai_token_consumption_total",
    "Total tokens consumed in LLM execution transactions",
    ["provider", "model", "token_type"]  # token_type: prompt, completion, total
)

# Counter for tracking tool execution count and success/failure outcomes
AI_TOOL_EXECUTION_TOTAL = Counter(
    "ai_tool_execution_total",
    "Total number of agent tool invocations",
    ["tool_name", "status"]  # status: success, failure
)

# Counter for tracking semantic cache hits vs misses
AI_CACHE_REQUESTS_TOTAL = Counter(
    "ai_cache_requests_total",
    "Total number of cache inquiries",
    ["outcome"]  # outcome: hit, miss
)


class AIMetricsCollector:
    """Helper wrapper to record metrics to Prometheus counters and histograms."""

    @staticmethod
    def record_latency(component: str, duration_seconds: float) -> None:
        """Record execution time for a component in seconds.

        Args:
            component: Component name.
            duration_seconds: Latency in seconds.
        """
        AI_LATENCY_SECONDS.labels(component_name=component).observe(duration_seconds)

    @staticmethod
    def record_tokens(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        """Record input and output tokens consumed.

        Args:
            provider: LLM provider enum name.
            model: Model name string.
            prompt_tokens: Input tokens used.
            completion_tokens: Output tokens generated.
        """
        AI_TOKEN_CONSUMPTION_TOTAL.labels(
            provider=provider,
            model=model,
            token_type="prompt",
        ).inc(prompt_tokens)
        AI_TOKEN_CONSUMPTION_TOTAL.labels(
            provider=provider,
            model=model,
            token_type="completion",
        ).inc(completion_tokens)
        AI_TOKEN_CONSUMPTION_TOTAL.labels(
            provider=provider,
            model=model,
            token_type="total",
        ).inc(prompt_tokens + completion_tokens)

    @staticmethod
    def record_tool_call(tool_name: str, success: bool) -> None:
        """Record a tool invocation status.

        Args:
            tool_name: Registered name of the tool.
            success: Execution outcome indicator.
        """
        status = "success" if success else "failure"
        AI_TOOL_EXECUTION_TOTAL.labels(
            tool_name=tool_name,
            status=status,
        ).inc()

    @staticmethod
    def record_cache_lookup(hit: bool) -> None:
        """Record a cache hit or miss event.

        Args:
            hit: True if cache lookup succeeded.
        """
        outcome = "hit" if hit else "miss"
        AI_CACHE_REQUESTS_TOTAL.labels(outcome=outcome).inc()
