"""
Thread-local request context for structured logging.

This module provides a RequestContext that stores per-request metadata
(request_id, user info, HTTP details, etc.) in thread-local storage.
The RequestContextFilter reads from this to inject fields into every
LogRecord emitted during the request lifecycle.

Usage in middleware:
    RequestContext.bind(request_id="abc-123", method="POST", ...)
    ...
    RequestContext.clear()

Usage in services (to add domain-specific context):
    RequestContext.update(entity_id="...", entity_type="user")

Usage in Celery tasks (carry correlation from HTTP to async):
    RequestContext.bind(
        request_id=task.request.id,
        correlation_id=original_correlation_id,
    )
"""

from __future__ import annotations

import threading
from typing import Any


_context_local = threading.local()


class RequestContext:
    """
    Thread-local storage for request-scoped log context.

    All values are stored as a flat dict. The RequestContextFilter
    reads this dict and merges it into every LogRecord.
    """

    @staticmethod
    def bind(**kwargs: Any) -> None:
        """
        Set initial request context. Called once per request by middleware.

        Replaces any existing context (important for thread reuse in WSGI).
        """
        _context_local.data = {k: v for k, v in kwargs.items() if v is not None}

    @staticmethod
    def update(**kwargs: Any) -> None:
        """
        Add or overwrite fields in the current context.

        Used by middleware to enrich with auth fields after authentication,
        and by services to add domain entity IDs.
        """
        data = getattr(_context_local, "data", None)
        if data is None:
            _context_local.data = {}
            data = _context_local.data
        for k, v in kwargs.items():
            if v is not None:
                data[k] = v

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Retrieve a single value from the current context."""
        data = getattr(_context_local, "data", None)
        if data is None:
            return default
        return data.get(key, default)

    @staticmethod
    def as_dict() -> dict[str, Any]:
        """Return a copy of the full current context."""
        data = getattr(_context_local, "data", None)
        if data is None:
            return {}
        return dict(data)

    @staticmethod
    def clear() -> None:
        """
        Remove all context. Called after each request completes.

        Critical for WSGI servers that reuse threads — prevents context
        leaking from one request to the next.
        """
        _context_local.data = None
