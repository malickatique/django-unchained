"""
Centralised PII and secret masking for log payloads.

This module provides functions to sanitise request/response bodies,
headers, and query parameters before they enter the log stream.

Masking rules are defined in constants.py. This module only applies them.

Design principles:
    - Never mutate the original data — always return a new dict.
    - Field name matching is case-insensitive.
    - Nested dicts/lists are traversed recursively up to MAX_SANITIZE_DEPTH.
    - Values exceeding MAX_FIELD_VALUE_LENGTH are truncated.
    - Binary/file content is never logged — only metadata.
"""

from __future__ import annotations

from typing import Any

from common.logging.constants import (
    ALLOWED_REQUEST_HEADERS,
    ALLOWED_RESPONSE_HEADERS,
    EMAIL_MASKED_FIELDS,
    FULLY_MASKED_FIELDS,
    MAX_FIELD_VALUE_LENGTH,
    MAX_SANITIZE_DEPTH,
    PARTIALLY_MASKED_FIELDS,
    PHONE_MASKED_FIELDS,
    REDACTED_FIELDS,
)


# ── Public API ───────────────────────────────────────────────────────


def sanitize_body(data: Any, *, depth: int = 0) -> Any:
    """
    Recursively sanitise a request/response body (parsed JSON).

    Returns a new structure with sensitive fields masked/redacted.
    """
    if depth >= MAX_SANITIZE_DEPTH:
        return "[TRUNCATED — max depth]"

    if isinstance(data, dict):
        return {
            key: _mask_field(key, value, depth=depth)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            sanitize_body(item, depth=depth + 1) for item in data[:50]
        ]

    return _truncate_value(data)


def sanitize_headers(
    headers: dict[str, str],
    *,
    allowed: frozenset[str] | None = None,
) -> dict[str, str]:
    """
    Filter headers to only allowed keys.

    Headers not in the allowlist are dropped entirely (not masked).
    """
    if allowed is None:
        allowed = ALLOWED_REQUEST_HEADERS

    result = {}
    for key, value in headers.items():
        lower_key = key.lower()
        if lower_key in allowed:
            result[lower_key] = value
    return result


def sanitize_request_headers(headers: dict[str, str]) -> dict[str, str]:
    """Sanitise request headers using the request allowlist."""
    return sanitize_headers(headers, allowed=ALLOWED_REQUEST_HEADERS)


def sanitize_response_headers(headers: dict[str, str]) -> dict[str, str]:
    """Sanitise response headers using the response allowlist."""
    return sanitize_headers(headers, allowed=ALLOWED_RESPONSE_HEADERS)


def sanitize_query_params(params: dict[str, str]) -> dict[str, str]:
    """
    Sanitise query parameters — mask values of sensitive keys.

    Non-sensitive keys keep their values (useful for debugging pagination,
    filtering, etc.).
    """
    result = {}
    for key, value in params.items():
        lower_key = key.lower()
        if _is_sensitive_field(lower_key):
            result[key] = "***"
        else:
            result[key] = _truncate_value(value)
    return result


def body_summary(data: Any) -> dict[str, Any]:
    """
    Produce a lightweight body summary for logging — field names and types,
    no values. Used when full body logging is disabled.
    """
    if isinstance(data, dict):
        return {
            "field_count": len(data),
            "fields": list(data.keys())[:20],
        }
    if isinstance(data, list):
        return {
            "item_count": len(data),
            "item_type": type(data[0]).__name__ if data else "empty",
        }
    return {"type": type(data).__name__}


# ── Masking functions ────────────────────────────────────────────────


def mask_email(value: str) -> str:
    """Mask email: m***@gmail.com"""
    if not isinstance(value, str) or "@" not in value:
        return "***"
    local, domain = value.rsplit("@", 1)
    if len(local) <= 1:
        return f"***@{domain}"
    return f"{local[0]}***@{domain}"


def mask_phone(value: str) -> str:
    """Mask phone: show last 4 digits → ***1234"""
    if not isinstance(value, str):
        return "***"
    digits = "".join(c for c in value if c.isdigit())
    if len(digits) <= 4:
        return "***"
    return f"***{digits[-4:]}"


def mask_partial(value: str) -> str:
    """Partial mask: show last 4 characters → ***4567"""
    if not isinstance(value, str):
        return "***"
    if len(value) <= 4:
        return "***"
    return f"***{value[-4:]}"


# ── Internal helpers ─────────────────────────────────────────────────


def _mask_field(key: str, value: Any, *, depth: int) -> Any:
    """Apply the correct masking strategy based on field name."""
    lower_key = key.lower()

    if lower_key in REDACTED_FIELDS:
        return "[REDACTED]"

    if lower_key in FULLY_MASKED_FIELDS:
        return "***"

    if lower_key in PARTIALLY_MASKED_FIELDS:
        return mask_partial(str(value)) if value is not None else None

    if lower_key in EMAIL_MASKED_FIELDS:
        return mask_email(str(value)) if value is not None else None

    if lower_key in PHONE_MASKED_FIELDS:
        return mask_phone(str(value)) if value is not None else None

    # Recurse into nested structures
    if isinstance(value, dict):
        return sanitize_body(value, depth=depth + 1)

    if isinstance(value, list):
        return sanitize_body(value, depth=depth + 1)

    return _truncate_value(value)


def _is_sensitive_field(lower_key: str) -> bool:
    """Check if a field name matches any sensitive category."""
    return (
        lower_key in FULLY_MASKED_FIELDS
        or lower_key in PARTIALLY_MASKED_FIELDS
        or lower_key in EMAIL_MASKED_FIELDS
        or lower_key in PHONE_MASKED_FIELDS
        or lower_key in REDACTED_FIELDS
    )


def _truncate_value(value: Any) -> Any:
    """Truncate string values exceeding the max length."""
    if isinstance(value, str) and len(value) > MAX_FIELD_VALUE_LENGTH:
        return f"{value[:MAX_FIELD_VALUE_LENGTH]}...[truncated]"
    return value
