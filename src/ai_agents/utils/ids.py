"""ID generation utilities for request, session, and trace tracking."""

import uuid


def generate_uuid() -> str:
    """Generate a standard version 4 UUID string.

    Returns:
        A unique 36-character UUID string.
    """
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """Generate a unique request tracking ID.

    Returns:
        UUID string prefixed for easy identification.
    """
    return f"req_{generate_uuid()}"


def generate_conversation_id() -> str:
    """Generate a unique conversation tracking ID.

    Returns:
        UUID string prefixed for easy identification.
    """
    return f"conv_{generate_uuid()}"


def generate_trace_id() -> str:
    """Generate a 32-character hexadecimal trace ID for OpenTelemetry compatibility.

    Returns:
        Hex-encoded string of a random 16-byte integer.
    """
    return uuid.uuid4().hex
