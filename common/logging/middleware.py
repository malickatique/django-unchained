"""
Request logging middleware — the entry and exit point for access logs.

Responsibilities:
    1. Extract or generate request_id and correlation_id.
    2. Populate the thread-local RequestContext with HTTP metadata.
    3. Log http.request.received on entry.
    4. Log http.response.sent on exit (with duration, status, outcome).
    5. Set X-Request-Id on the response header for client debugging.
    6. Clean up RequestContext after each request.

Placement in MIDDLEWARE (config/settings/base.py):
    After AuthenticationMiddleware (so request.user is available),
    before AuditMiddleware (so log context is available for audit).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from common.logging.constants import (
    EXCLUDED_PATHS,
    Events,
    LogCategory,
    MAX_BODY_LOG_SIZE,
    NO_BODY_LOG_PATHS,
)
from common.logging.context import RequestContext
from common.logging.sanitizers import (
    body_summary,
    sanitize_body,
    sanitize_query_params,
    sanitize_request_headers,
    sanitize_response_headers,
)

access_logger = logging.getLogger(LogCategory.ACCESS)
security_logger = logging.getLogger(LogCategory.SECURITY)


class RequestLoggingMiddleware:
    """
    Logs HTTP request/response lifecycle with structured context.

    Every request produces exactly two access log entries:
        1. http.request.received  (INFO)
        2. http.response.sent     (INFO for 2xx/3xx, WARNING for 4xx/5xx)

    All log entries within the request lifecycle share the same
    request_id via thread-local RequestContext.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip excluded paths (health checks, etc.)
        if request.path in EXCLUDED_PATHS:
            return self.get_response(request)

        # ── Phase 1: Extract/generate correlation IDs ────────────
        request_id = (
            request.META.get("HTTP_X_REQUEST_ID")
            or str(uuid.uuid4())
        )
        correlation_id = (
            request.META.get("HTTP_X_CORRELATION_ID")
            or request_id
        )

        # ── Phase 2: Build request context ───────────────────────
        api_surface = self._derive_api_surface(request.path)
        route_name = self._get_route_name(request)

        RequestContext.bind(
            request_id=request_id,
            correlation_id=correlation_id,
            method=request.method,
            path=request.path,
            route_name=route_name,
            api_surface=api_surface,
            client_ip=self._get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            content_type=request.content_type,
            content_length=request.META.get("CONTENT_LENGTH", "0"),
        )

        # Enrich with auth info if user is already authenticated
        # (AuthenticationMiddleware runs before us)
        self._enrich_auth_context(request)

        # ── Phase 3: Log request received ────────────────────────
        start_time = time.monotonic()
        self._log_request_received(request)

        # ── Phase 4: Process request ─────────────────────────────
        response = self.get_response(request)

        # ── Phase 5: Log response sent ───────────────────────────
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        self._log_response_sent(request, response, duration_ms)

        # ── Phase 6: Set response header and clean up ────────────
        response["X-Request-Id"] = request_id
        RequestContext.clear()

        return response

    # ── Request logging ──────────────────────────────────────────────

    def _log_request_received(self, request: HttpRequest) -> None:
        """Log the incoming request with sanitised metadata."""
        extra: dict[str, Any] = {
            "event": Events.HTTP_REQUEST_RECEIVED,
            "category": "access",
        }

        # Sanitised headers
        raw_headers = self._extract_headers(request)
        extra["headers"] = sanitize_request_headers(raw_headers)

        # Query params
        if request.GET:
            extra["query_params"] = sanitize_query_params(
                dict(request.GET.items())
            )

        # Body summary/sanitised body (dev only, non-file endpoints)
        body_info = self._get_request_body_info(request)
        if body_info:
            extra["body"] = body_info

        access_logger.info(
            f"{request.method} {request.path}",
            extra=extra,
        )

    # ── Response logging ─────────────────────────────────────────────

    def _log_response_sent(
        self,
        request: HttpRequest,
        response: HttpResponse,
        duration_ms: float,
    ) -> None:
        """Log the outgoing response with status and duration."""
        status_code = response.status_code
        outcome = self._classify_outcome(status_code)

        extra: dict[str, Any] = {
            "event": Events.HTTP_RESPONSE_SENT,
            "category": "access",
            "status_code": status_code,
            "duration_ms": duration_ms,
            "outcome": outcome,
            "response_size": len(response.content) if hasattr(response, "content") else 0,
        }

        # Sanitised response headers
        extra["response_headers"] = sanitize_response_headers(
            dict(response.items())
        )

        message = f"{request.method} {request.path} -> {status_code} ({duration_ms}ms)"

        # Log level based on status code
        if status_code >= 500:
            access_logger.error(message, extra=extra)
        elif status_code >= 400:
            access_logger.warning(message, extra=extra)
        else:
            access_logger.info(message, extra=extra)

        # Security logging for auth/permission failures
        if status_code == 401:
            security_logger.warning(
                f"Authentication failed: {request.method} {request.path}",
                extra={
                    "event": Events.AUTH_FAILED,
                    "category": "security",
                    "status_code": status_code,
                },
            )
        elif status_code == 403:
            security_logger.warning(
                f"Permission denied: {request.method} {request.path}",
                extra={
                    "event": Events.PERMISSION_DENIED,
                    "category": "security",
                    "status_code": status_code,
                },
            )

    # ── Helper methods ───────────────────────────────────────────────

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """Extract client IP from X-Forwarded-For or REMOTE_ADDR."""
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            # Take the first IP (client IP) from the chain
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    @staticmethod
    def _derive_api_surface(path: str) -> str | None:
        """Derive API surface from URL path prefix."""
        if "/v1/me/" in path or "/api/v1/me/" in path:
            return "customer"
        if "/v1/admin/" in path or "/api/v1/admin/" in path:
            return "admin"
        if "/v1/meta/" in path or "/api/v1/meta/" in path:
            return "meta"
        return None

    @staticmethod
    def _get_route_name(request: HttpRequest) -> str | None:
        """Get the Django URL name or view function name."""
        resolver_match = getattr(request, "resolver_match", None)
        if resolver_match:
            return (
                resolver_match.url_name
                or resolver_match.view_name
                or None
            )
        return None

    @staticmethod
    def _enrich_auth_context(request: HttpRequest) -> None:
        """Add authenticated user info to the log context."""
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            RequestContext.update(
                auth_user_id=str(user.id),
                auth_user_type=getattr(user, "user_type", None),
                organisation_id=str(user.organisation_id)
                if getattr(user, "organisation_id", None)
                else None,
            )

    @staticmethod
    def _extract_headers(request: HttpRequest) -> dict[str, str]:
        """Extract HTTP headers from Django's META dict."""
        headers = {}
        for key, value in request.META.items():
            if key.startswith("HTTP_"):
                # HTTP_X_REQUEST_ID → x-request-id
                header_name = key[5:].lower().replace("_", "-")
                headers[header_name] = value
            elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                headers[key.lower().replace("_", "-")] = value
        return headers

    def _get_request_body_info(self, request: HttpRequest) -> dict[str, Any] | None:
        """
        Get sanitised request body info for logging.

        Returns:
            - None for excluded paths or file uploads
            - body_summary for large bodies or in production
            - sanitize_body for small bodies in development
        """
        # Skip file upload endpoints
        if any(request.path.startswith(p) for p in NO_BODY_LOG_PATHS):
            return None

        # Skip if no body
        content_length = int(request.META.get("CONTENT_LENGTH") or 0)
        if content_length == 0:
            return None

        # Skip multipart (file uploads)
        content_type = request.content_type or ""
        if "multipart" in content_type:
            return {"note": "multipart/form-data — body not logged"}

        # Try to parse JSON body
        try:
            body_bytes = request.body
        except Exception:
            return None

        if len(body_bytes) > MAX_BODY_LOG_SIZE:
            return {"note": f"body too large ({len(body_bytes)} bytes)"}

        try:
            parsed = json.loads(body_bytes)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"note": f"non-JSON body ({content_type}, {len(body_bytes)} bytes)"}

        # In production: summary only. In dev: sanitised full body.
        if settings.DEBUG:
            return sanitize_body(parsed)
        return body_summary(parsed)

    @staticmethod
    def _classify_outcome(status_code: int) -> str:
        """Classify HTTP status code into outcome category."""
        if 200 <= status_code < 400:
            return "success"
        if 400 <= status_code < 500:
            return "client_error"
        return "server_error"
