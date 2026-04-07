"""
Common error codes for the API response contract.

These codes are machine-readable identifiers that consumers use to branch logic.
Keep this set tight — only add a new code when the frontend needs to take a
*different action* based on it. If a toast message is sufficient, use an existing
generic code with a descriptive `message`.

App-specific codes (e.g. ORDER_ALREADY_SUBMITTED) belong in
`apps/<app>/exceptions/codes.py` and should follow the same TextChoices pattern.
"""

from django.db import models


class ErrorCode(models.TextChoices):
    """
    Coarse error codes shared across all API surfaces.

    Categories:
      - Validation & input
      - Authentication & access
      - Resource state
      - Domain / business logic
      - Rate limiting
      - System / infrastructure
    """

    # ── Validation & Input ───────────────────────────────────────────
    VALIDATION_ERROR = "VALIDATION_ERROR", "Validation error"
    BAD_REQUEST = "BAD_REQUEST", "Bad request"

    # ── Authentication & Access ──────────────────────────────────────
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR", "Authentication error"
    PERMISSION_DENIED = "PERMISSION_DENIED", "Permission denied"
    TOKEN_EXPIRED = "TOKEN_EXPIRED", "Token expired"

    # ── Resource State ───────────────────────────────────────────────
    NOT_FOUND = "NOT_FOUND", "Not found"
    CONFLICT = "CONFLICT", "Conflict"
    GONE = "GONE", "Gone"

    # ── Domain / Business Logic ──────────────────────────────────────
    INVALID_STATE_TRANSITION = (
        "INVALID_STATE_TRANSITION",
        "Invalid state transition",
    )
    BUSINESS_RULE_VIOLATION = (
        "BUSINESS_RULE_VIOLATION",
        "Business rule violation",
    )

    # ── Rate Limiting ────────────────────────────────────────────────
    RATE_LIMITED = "RATE_LIMITED", "Rate limited"

    # ── System / Infrastructure ──────────────────────────────────────
    SYSTEM_ERROR = "SYSTEM_ERROR", "System error"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE", "Service unavailable"


# ── HTTP status → default error code mapping ────────────────────────
# Used by the exception handler when no explicit error_code is provided.
HTTP_STATUS_TO_ERROR_CODE: dict[int, str] = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.AUTHENTICATION_ERROR,
    403: ErrorCode.PERMISSION_DENIED,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.BAD_REQUEST,
    409: ErrorCode.CONFLICT,
    410: ErrorCode.GONE,
    415: ErrorCode.BAD_REQUEST,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.RATE_LIMITED,
    500: ErrorCode.SYSTEM_ERROR,
    502: ErrorCode.SERVICE_UNAVAILABLE,
    503: ErrorCode.SERVICE_UNAVAILABLE,
    504: ErrorCode.SERVICE_UNAVAILABLE,
}
