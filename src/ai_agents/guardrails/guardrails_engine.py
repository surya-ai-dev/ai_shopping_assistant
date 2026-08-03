"""Guardrails engine orchestrating pre-LLM input validation and post-LLM output filtering."""

import time
from typing import Any

from src.ai_agents.guardrails.fallback import (
    DefaultFallbackGenerator,
    FallbackGenerator,
)
from src.ai_agents.guardrails.prompt_builder import (
    DefaultPromptBuilder,
    PromptBuilder,
)
from src.ai_agents.guardrails.response_filter import (
    DefaultResponseFilter,
    ResponseFilter,
)
from src.ai_agents.guardrails.result import GuardrailResult, GuardrailStatus
from src.ai_agents.guardrails.validators import (
    CapabilityValidator,
    ConversationValidator,
    DomainValidator,
    GuardrailValidator,
)
from src.ai_agents.logging import get_ai_logger


class GuardrailsEngine:
    """Orchestrator for the AI Guardrails Layer implementing Pre-LLM and Post-LLM pipelines.

    This engine is completely stateless and deterministic, validating requests, building
    prompts, and filtering responses based on business policy constraints.
    """

    _validators: list[GuardrailValidator]
    _prompt_builder: PromptBuilder
    _response_filter: ResponseFilter
    _fallback_generator: FallbackGenerator

    def __init__(
        self,
        validators: list[GuardrailValidator] | None = None,
        prompt_builder: PromptBuilder | None = None,
        response_filter: ResponseFilter | None = None,
        fallback_generator: FallbackGenerator | None = None,
    ) -> None:
        """Initialize the GuardrailsEngine with configurable components.

        Args:
            validators: Input query constraint checkers.
            prompt_builder: Compiler for system instruction prompts.
            response_filter: Inspector for LLM outputs.
            fallback_generator: Supplier of standardized rejects responses.
        """
        default_validators: list[GuardrailValidator] = [
            CapabilityValidator(),
            DomainValidator(),
            ConversationValidator(),
        ]
        self._validators = validators if validators is not None else default_validators
        self._prompt_builder = prompt_builder or DefaultPromptBuilder()
        self._response_filter = response_filter or DefaultResponseFilter()
        self._fallback_generator = fallback_generator or DefaultFallbackGenerator()
        self._logger = get_ai_logger("GuardrailsEngine")

    def check_request(self, query: str, metadata: dict[str, Any] | None = None) -> GuardrailResult:
        """Execute the Pre-LLM Pipeline: validate query bounds and compile system prompt.

        Args:
            query: The raw input user query.
            metadata: Context metadata (e.g. turn_count, started_at).

        Returns:
            GuardrailResult resolving ALLOW or REJECT.
        """
        start_time = time.perf_counter()

        meta_dict = metadata or {}
        correlation_id = (
            meta_dict.get("request_id")
            or meta_dict.get("trace_id")
            or "unknown_correlation_id"
        )

        try:
            # 1. Run all validators
            for validator in self._validators:
                v_start = time.perf_counter()
                is_allowed, reason = validator.validate(query, meta_dict)
                v_duration = (time.perf_counter() - v_start) * 1000.0

                # Log evaluation metrics safely (no user query text)
                self._logger.info(
                    "Guardrail validator evaluated",
                    validator_name=validator.name,
                    execution_time_ms=v_duration,
                    decision="ALLOW" if is_allowed else "REJECT",
                    correlation_id=correlation_id,
                )

                if not is_allowed:
                    # Resolve appropriate fallback string
                    if validator.name == "DomainValidator":
                        fallback = self._fallback_generator.unsupported_domain()
                        violated = "DomainPolicy"
                    elif validator.name == "CapabilityValidator":
                        fallback = self._fallback_generator.unsupported_capability()
                        violated = "CapabilityPolicy"
                    else:
                        fallback = self._fallback_generator.unsafe_response()
                        violated = "ConversationPolicy"

                    total_duration = (time.perf_counter() - start_time) * 1000.0
                    return GuardrailResult(
                        status=GuardrailStatus.REJECT,
                        reason=reason,
                        fallback_response=fallback,
                        violated_policy=violated,
                        validator_name=validator.name,
                        metadata={
                            "correlation_id": correlation_id,
                            "validator_executed": validator.name,
                        },
                        execution_time_ms=total_duration,
                    )

            # 2. Build system instructions prompt if all validators pass
            p_start = time.perf_counter()
            system_prompt = self._prompt_builder.build_system_prompt(query)
            p_duration = (time.perf_counter() - p_start) * 1000.0

            total_duration = (time.perf_counter() - start_time) * 1000.0

            self._logger.info(
                "Guardrail request checks completed successfully",
                decision="ALLOW",
                prompt_build_time_ms=p_duration,
                execution_time_ms=total_duration,
                correlation_id=correlation_id,
            )

            return GuardrailResult(
                status=GuardrailStatus.ALLOW,
                system_prompt=system_prompt,
                metadata={
                    "correlation_id": correlation_id,
                    "validators_executed": [v.name for v in self._validators],
                    "prompt_build_time_ms": p_duration,
                },
                execution_time_ms=total_duration,
            )

        except Exception as exc:
            # Safe boundary catch: log exception context and return deterministic reject
            self._logger.exception(
                "Unexpected failure inside guardrail pre-LLM pipeline",
                correlation_id=correlation_id,
            )
            total_duration = (time.perf_counter() - start_time) * 1000.0
            return GuardrailResult(
                status=GuardrailStatus.REJECT,
                reason=f"Internal guardrails engine check failure: {type(exc).__name__}",
                fallback_response=self._fallback_generator.unsafe_response(),
                violated_policy="SystemFaultPolicy",
                validator_name="GuardrailsEngine",
                metadata={
                    "correlation_id": correlation_id,
                    "error_class": type(exc).__name__,
                },
                execution_time_ms=total_duration,
            )

    def check_response(
        self, query: str, response_text: str, metadata: dict[str, Any] | None = None
    ) -> GuardrailResult:
        """Execute the Post-LLM Pipeline: filter LLM output against response policies.

        Args:
            query: The user query context string.
            response_text: The generated LLM response string.
            metadata: Context metadata.

        Returns:
            GuardrailResult resolving ALLOW, MODIFY, or REJECT.
        """
        start_time = time.perf_counter()

        meta_dict = metadata or {}
        correlation_id = (
            meta_dict.get("request_id")
            or meta_dict.get("trace_id")
            or "unknown_correlation_id"
        )

        try:
            # Run the output response filter
            f_start = time.perf_counter()
            status, reason = self._response_filter.filter_response(query, response_text)
            f_duration = (time.perf_counter() - f_start) * 1000.0

            total_duration = (time.perf_counter() - start_time) * 1000.0

            # Log check result safely (no response text in logs)
            self._logger.info(
                "Guardrail response filter evaluated",
                filter_name="DefaultResponseFilter",
                execution_time_ms=f_duration,
                decision=status.value,
                correlation_id=correlation_id,
            )

            if status == GuardrailStatus.REJECT:
                fallback = self._fallback_generator.unsafe_response()
                return GuardrailResult(
                    status=GuardrailStatus.REJECT,
                    reason=reason,
                    fallback_response=fallback,
                    violated_policy="ResponsePolicy",
                    validator_name="ResponseFilter",
                    metadata={
                        "correlation_id": correlation_id,
                        "response_filter_time_ms": f_duration,
                    },
                    execution_time_ms=total_duration,
                )

            return GuardrailResult(
                status=GuardrailStatus.ALLOW,
                metadata={
                    "correlation_id": correlation_id,
                    "response_filter_time_ms": f_duration,
                },
                execution_time_ms=total_duration,
            )

        except Exception as exc:
            # Safe boundary catch: log exception context and return deterministic reject
            self._logger.exception(
                "Unexpected failure inside guardrail post-LLM pipeline",
                correlation_id=correlation_id,
            )
            total_duration = (time.perf_counter() - start_time) * 1000.0
            return GuardrailResult(
                status=GuardrailStatus.REJECT,
                reason=f"Internal guardrails engine check failure: {type(exc).__name__}",
                fallback_response=self._fallback_generator.unsafe_response(),
                violated_policy="SystemFaultPolicy",
                validator_name="GuardrailsEngine",
                metadata={
                    "correlation_id": correlation_id,
                    "error_class": type(exc).__name__,
                },
                execution_time_ms=total_duration,
            )
