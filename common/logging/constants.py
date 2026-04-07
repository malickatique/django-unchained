"""
Logging constants — the stable contract for structured logging.

This module defines:
    - Service name (identify this service in centralised log aggregators)
    - Event taxonomy (stable, dot-namespaced event names)
    - Field masking registries (PII/secret protection)
    - Header allowlists (what gets logged from HTTP headers)
    - Excluded paths (health checks, etc.)
    - Log category names

All event names and masking rules are centralised here so that:
    1. Developers don't invent ad-hoc event names.
    2. Masking policy is enforced in one place, not scattered across code.
    3. Changes to the logging contract are reviewable in one diff.

NOTE (for cloners): Set the LOG_SERVICE_NAME env var, and update
LogCategory prefixes to match your project before going to production.
"""

import os


# ── Service metadata ─────────────────────────────────────────────────
# SERVICE_NAME: identifies this service in a centralised log aggregator
# (ELK, Datadog, CloudWatch, etc.) where logs from multiple services
# share one index.
#
# Configure via environment variable — no code change needed when cloning:
#   LOG_SERVICE_NAME=my-project  (in .env or container env)

SERVICE_NAME = os.environ.get("LOG_SERVICE_NAME", "django-unchained")


# ── Log categories ───────────────────────────────────────────────────
# Used as logger name prefixes. Each maps to a separate handler/file.
# Change the "app." prefix to something project-specific when cloning.

class LogCategory:
    ACCESS = "app.access"
    APP = "app.app"
    SECURITY = "app.security"
    ERROR = "app.error"
    INFRA = "app.infra"


# ── Event taxonomy ───────────────────────────────────────────────────
# Stable, dot-namespaced. Search/alert on these, not message strings.

class Events:
    """Stable event names — never rename, only deprecate and add new."""

    # HTTP lifecycle (access logs)
    HTTP_REQUEST_RECEIVED = "http.request.received"
    HTTP_RESPONSE_SENT = "http.response.sent"

    # Domain — User
    USER_CREATED = "domain.user.created"
    USER_UPDATED = "domain.user.updated"
    USER_DEACTIVATED = "domain.user.deactivated"

    # Security
    AUTH_SUCCEEDED = "security.auth.succeeded"
    AUTH_FAILED = "security.auth.failed"
    PERMISSION_DENIED = "security.permission.denied"
    SENSITIVE_ACTION = "security.sensitive_action.performed"
    RATE_LIMIT_HIT = "security.rate_limit.hit"
    TOKEN_EXPIRED = "security.token.expired"

    # Error
    ERROR_UNHANDLED = "error.unhandled"
    ERROR_VALIDATION = "error.validation"
    ERROR_BUSINESS_RULE = "error.business_rule"
    ERROR_DATABASE = "error.database"
    ERROR_INTEGRATION = "error.integration"

    # Infrastructure / Integration
    EXTERNAL_REQUEST_SENT = "infra.external.request.sent"
    EXTERNAL_RESPONSE_RECEIVED = "infra.external.response.received"
    EXTERNAL_TIMEOUT = "infra.external.timeout"
    DB_SLOW_QUERY = "infra.db.slow_query"


# ── Masking configuration ────────────────────────────────────────────
# Field names are matched case-insensitively against JSON keys and
# query parameter names.

# Full mask → replaced with "***"
FULLY_MASKED_FIELDS: frozenset[str] = frozenset({
    "password",
    "password1",
    "password2",
    "old_password",
    "new_password",
    "confirm_password",
    "pin",
    "cvv",
    "cvc",
    "secret",
    "secret_key",
    "private_key",
    "token",
    "access_token",
    "refresh_token",
    "otp",
    "otp_code",
    "verification_code",
    "api_key",
    "signature",
})

# Partial mask → show last 4 characters, rest replaced with ***
PARTIALLY_MASKED_FIELDS: frozenset[str] = frozenset({
    "passport_number",
    "iban",
    "account_number",
    "card_number",
    "pan",
    "national_id",
    "tax_id",
    "ssn",
    "driving_license_number",
})

# Email mask → show first char + "***" + domain (m***@gmail.com)
EMAIL_MASKED_FIELDS: frozenset[str] = frozenset({
    "email",
    "email_address",
    "contact_email",
})

# Phone mask → show last 4 digits (***1234)
PHONE_MASKED_FIELDS: frozenset[str] = frozenset({
    "phone",
    "phone_number",
    "mobile",
    "mobile_number",
    "contact_number",
})

# Never log these fields at all — replace with "[REDACTED]"
REDACTED_FIELDS: frozenset[str] = frozenset({
    "biometric_data",
    "fingerprint",
    "face_image",
    "selfie",
    "signature_image",
    "document_content",
    "file_content",
    "base64_data",
    "date_of_birth",
    "dob",
})


# ── Header allowlist ─────────────────────────────────────────────────
# Only these headers are logged. Everything else is dropped.

ALLOWED_REQUEST_HEADERS: frozenset[str] = frozenset({
    "content-type",
    "content-length",
    "accept",
    "accept-language",
    "user-agent",
    "x-request-id",
    "x-correlation-id",
    "x-forwarded-for",
    "x-forwarded-proto",
})

ALLOWED_RESPONSE_HEADERS: frozenset[str] = frozenset({
    "content-type",
    "content-length",
    "x-request-id",
    "cache-control",
})


# ── Paths excluded from access logging ───────────────────────────────
# Health checks and similar high-frequency, low-value endpoints.

EXCLUDED_PATHS: frozenset[str] = frozenset({
    "/healthz/",
    "/readyz/",
    "/favicon.ico",
})


# ── Body logging policy ─────────────────────────────────────────────
# Paths where request/response bodies should NEVER be logged,
# even in dev, because they contain binary data or large files.
# Add your file upload or streaming endpoints here when cloning.
# Example: "/api/v1/uploads/", "/api/v1/documents/"

NO_BODY_LOG_PATHS: frozenset[str] = frozenset()

# Maximum field value length before truncation in body summaries
MAX_FIELD_VALUE_LENGTH = 200

# Maximum depth for nested dict traversal during sanitisation
MAX_SANITIZE_DEPTH = 5

# Maximum size of request/response body to attempt sanitised logging (bytes)
MAX_BODY_LOG_SIZE = 10_000
