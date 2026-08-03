"""Security policies evaluating scan reports to determine final safety decisions."""

from typing import Protocol

from src.ai_agents.security.result import (
    ScanReport,
    SecuritySeverity,
    SecurityStatus,
    ThreatType,
)


class SecurityPolicyEngine(Protocol):
    """Protocol defining the interface for security policy engines."""

    def evaluate(
        self, scan_report: ScanReport
    ) -> tuple[SecurityStatus, ThreatType, SecuritySeverity, str | None]:
        """Evaluate the scan report to determine safety status, threat type, severity, and reason.

        Args:
            scan_report: The aggregated report of validator and detector runs.

        Returns:
            A tuple containing:
                - SecurityStatus (SAFE, WARNING, BLOCKED)
                - ThreatType
                - SecuritySeverity (LOW, MEDIUM, HIGH, CRITICAL)
                - reason: Explanation of the decision or None if SAFE.
        """
        ...


class DefaultSecurityPolicyEngine:
    """Standard security policy engine implementing default mapping rules."""

    def evaluate(
        self, scan_report: ScanReport
    ) -> tuple[SecurityStatus, ThreatType, SecuritySeverity, str | None]:
        """Map validation and detection results to safety status, threat type, severity, and reasons.

        Evaluation order (highest priority threat first):
        1. SQL Injection -> BLOCKED, SQL_INJECTION, CRITICAL
        2. XSS -> BLOCKED, XSS, HIGH
        3. Prompt Injection -> BLOCKED, PROMPT_INJECTION, HIGH
        4. Jailbreak -> BLOCKED, JAILBREAK, HIGH
        5. Invalid Input -> BLOCKED, INVALID_INPUT, LOW
        6. Unsupported Category -> WARNING, UNSUPPORTED_CATEGORY, LOW
        7. Otherwise -> SAFE, NONE, LOW

        Args:
            scan_report: Aggregated ScanReport model.

        Returns:
            Decisions tuple (status, threat_type, severity, reason).
        """
        # Default fallback is SAFE
        status = SecurityStatus.SAFE
        threat_type = ThreatType.NONE
        severity = SecuritySeverity.LOW
        reason: str | None = None

        # 1. SQL Injection
        if scan_report.sql_injection_detected:
            status = SecurityStatus.BLOCKED
            threat_type = ThreatType.SQL_INJECTION
            severity = SecuritySeverity.CRITICAL
            reason = scan_report.sql_injection_reason

        # 2. XSS
        elif scan_report.xss_detected:
            status = SecurityStatus.BLOCKED
            threat_type = ThreatType.XSS
            severity = SecuritySeverity.HIGH
            reason = scan_report.xss_reason

        # 3. Prompt Injection
        elif scan_report.prompt_injection_detected:
            status = SecurityStatus.BLOCKED
            threat_type = ThreatType.PROMPT_INJECTION
            severity = SecuritySeverity.HIGH
            reason = scan_report.prompt_injection_reason

        # 4. Jailbreak
        elif scan_report.jailbreak_detected:
            status = SecurityStatus.BLOCKED
            threat_type = ThreatType.JAILBREAK
            severity = SecuritySeverity.HIGH
            reason = scan_report.jailbreak_reason

        # 5. Invalid Input
        elif not scan_report.input_valid:
            status = SecurityStatus.BLOCKED
            threat_type = ThreatType.INVALID_INPUT
            severity = SecuritySeverity.LOW
            reason = scan_report.input_error

        # 6. Unsupported Category
        elif not scan_report.category_valid:
            status = SecurityStatus.WARNING
            threat_type = ThreatType.UNSUPPORTED_CATEGORY
            severity = SecuritySeverity.LOW
            reason = scan_report.category_error

        return status, threat_type, severity, reason
