"""Security engine orchestrating sanitization, validations, detections, and policies."""

import time
from typing import Any

from src.ai_agents.logging import get_ai_logger
from src.ai_agents.security.detectors import (
    JailbreakDetector,
    PromptInjectionDetector,
    SecurityDetector,
    SQLInjectionDetector,
    XSSDetector,
)
from src.ai_agents.security.policies import (
    DefaultSecurityPolicyEngine,
    SecurityPolicyEngine,
)
from src.ai_agents.security.result import ScanReport, SecurityResult
from src.ai_agents.security.sanitizers import (
    DefaultRequestSanitizer,
    RequestSanitizer,
)
from src.ai_agents.security.validators import (
    CategoryValidator,
    InputValidator,
    SecurityValidator,
)


class SecurityEngine:
    """Entry point of the Security Layer orchestrating all checks.

    This engine sanitizes the query, runs configured validators and detectors,
    compiles a ScanReport, and queries a policy engine to determine the safety decision.
    """

    _sanitizer: RequestSanitizer
    _validators: list[SecurityValidator]
    _detectors: list[SecurityDetector]
    _policy_engine: SecurityPolicyEngine

    def __init__(
        self,
        sanitizer: RequestSanitizer | None = None,
        validators: list[SecurityValidator] | None = None,
        detectors: list[SecurityDetector] | None = None,
        policy_engine: SecurityPolicyEngine | None = None,
    ) -> None:
        """Initialize the SecurityEngine with customizable components.

        Args:
            sanitizer: Component for cleaning prompt input queries.
            validators: List of constraint/format check components.
            detectors: List of semantic/regex threat detection components.
            policy_engine: Policy component resolving safety status.
        """
        self._sanitizer = sanitizer if sanitizer is not None else DefaultRequestSanitizer()
        
        default_validators: list[SecurityValidator] = [InputValidator(), CategoryValidator()]
        self._validators = validators if validators is not None else default_validators
        
        default_detectors: list[SecurityDetector] = [
            PromptInjectionDetector(),
            JailbreakDetector(),
            SQLInjectionDetector(),
            XSSDetector(),
        ]
        self._detectors = detectors if detectors is not None else default_detectors
        
        self._policy_engine = policy_engine if policy_engine is not None else DefaultSecurityPolicyEngine()
        self._logger = get_ai_logger("SecurityEngine")

    def check_request(self, query: str, metadata: dict[str, Any] | None = None) -> SecurityResult:
        """Evaluate the safety of an incoming user query.

        This method follows the sequence:
        1. Sanitize request
        2. Run validators
        3. Run detectors
        4. Evaluate ScanReport
        5. Map to SecurityResult

        Args:
            query: The raw query prompt string.
            metadata: Request context metadata containing IDs.

        Returns:
            SecurityResult containing the security status and metadata.
        """
        start_time = time.perf_counter()

        # Extract correlation ID for logging
        meta_dict = metadata or {}
        correlation_id = (
            meta_dict.get("request_id")
            or meta_dict.get("trace_id")
            or "unknown_correlation_id"
        )

        # 1. Request Sanitizer
        sanitized = self._sanitizer.sanitize(query)

        scan = ScanReport()
        detected_names: list[str] = []
        confidences: list[float] = []

        # 2. Validators
        # Note: Validators run on the sanitized query (except empty validation which can catch raw blank queries).
        # We also pass raw metadata.
        for validator in self._validators:
            v_start = time.perf_counter()
            is_valid, err_msg = validator.validate(sanitized, meta_dict)
            v_duration = (time.perf_counter() - v_start) * 1000.0

            # Log validation decision without raw query content
            self._logger.info(
                "Security validator evaluated",
                validator_name=validator.name,
                execution_time_ms=v_duration,
                decision="VALID" if is_valid else "INVALID",
                threat_detected=str(not is_valid),
                correlation_id=correlation_id,
            )

            if not is_valid:
                detected_names.append(validator.name)
                confidences.append(1.0)
                if validator.name == "InputValidator":
                    scan.input_valid = False
                    scan.input_error = err_msg
                elif validator.name == "CategoryValidator":
                    scan.category_valid = False
                    scan.category_error = err_msg

        # 3. Detectors
        # Detectors scan the sanitized query for malicious injection patterns.
        for detector in self._detectors:
            d_start = time.perf_counter()
            is_threat, reason, confidence = detector.detect(sanitized)
            d_duration = (time.perf_counter() - d_start) * 1000.0

            # Log detector decision without raw query content
            self._logger.info(
                "Security detector evaluated",
                detector_name=detector.name,
                execution_time_ms=d_duration,
                decision="THREAT_FOUND" if is_threat else "CLEAN",
                threat_detected=str(is_threat),
                correlation_id=correlation_id,
            )

            if is_threat:
                detected_names.append(detector.name)
                confidences.append(confidence)
                if isinstance(detector, PromptInjectionDetector):
                    scan.prompt_injection_detected = True
                    scan.prompt_injection_reason = reason
                    scan.prompt_injection_confidence = confidence
                elif isinstance(detector, JailbreakDetector):
                    scan.jailbreak_detected = True
                    scan.jailbreak_reason = reason
                    scan.jailbreak_confidence = confidence
                elif isinstance(detector, SQLInjectionDetector):
                    scan.sql_injection_detected = True
                    scan.sql_injection_reason = reason
                    scan.sql_injection_confidence = confidence
                elif isinstance(detector, XSSDetector):
                    scan.xss_detected = True
                    scan.xss_reason = reason
                    scan.xss_confidence = confidence

        # 4. Policy Engine
        status, threat_type, severity, reason = self._policy_engine.evaluate(scan)

        # Calculate combined confidence (max confidence, or 1.0 for SAFE requests)
        final_confidence = max(confidences) if confidences else 1.0

        total_duration = (time.perf_counter() - start_time) * 1000.0

        # Log complete orchestration decision
        self._logger.info(
            "Security evaluation completed",
            status=status.value,
            threat_type=threat_type.value,
            severity=severity.value,
            execution_time_ms=total_duration,
            correlation_id=correlation_id,
        )

        return SecurityResult(
            status=status,
            threat_type=threat_type,
            severity=severity,
            reason=reason,
            detected_threats=detected_names,
            sanitized_query=sanitized,
            confidence=final_confidence,
            metadata={
                "correlation_id": correlation_id,
                "validators_executed": [v.name for v in self._validators],
                "detectors_executed": [d.name for d in self._detectors],
            },
            execution_time_ms=total_duration,
            scan_report=scan,
        )
