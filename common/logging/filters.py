"""
Logging filters that inject request context into every LogRecord.

The RequestContextFilter reads from the thread-local RequestContext
and adds all stored fields to the LogRecord. This means any logger
in the application automatically includes request_id, user info,
HTTP details, etc. — without the caller having to pass them manually.

Wired into Django's LOGGING config:
    "filters": {
        "request_context": {
            "()": "common.logging.filters.RequestContextFilter",
        },
    }
"""

from __future__ import annotations

import logging

from common.logging.context import RequestContext


class RequestContextFilter(logging.Filter):
    """
    Injects request-scoped context into every log record.

    Fields injected (when present in context):
        - request_id, correlation_id, trace_id, span_id
        - method, path, route_name, api_surface, query_params
        - client_ip, user_agent, content_type, content_length
        - auth_user_id, auth_user_type, organisation_id
        - category (log category: access/app/security/error/infra)

    Plus any domain-specific fields added via RequestContext.update().
    """

    # Default values for fields that consumers might expect to exist.
    # Prevents KeyError in formatters if context is empty (e.g., during
    # startup, management commands, or Celery tasks without context).
    _DEFAULTS: dict[str, str | None] = {
        "request_id": None,
        "correlation_id": None,
        "trace_id": None,
        "span_id": None,
        "method": None,
        "path": None,
        "route_name": None,
        "api_surface": None,
        "client_ip": None,
        "user_agent": None,
        "auth_user_id": None,
        "auth_user_type": None,
        "organisation_id": None,
        "event": None,
        "category": None,
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add context fields to the record. Always returns True
        (this filter enriches, it never drops records).
        """
        # Set defaults first (so JSON formatter always has the keys)
        for key, default in self._DEFAULTS.items():
            if not hasattr(record, key):
                setattr(record, key, default)

        # Overlay with actual request context
        context = RequestContext.as_dict()
        for key, value in context.items():
            setattr(record, key, value)

        return True
