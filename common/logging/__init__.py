"""
Structured logging package for django-unchained.

Public API:
    - RequestContext: thread-local request context for log enrichment
    - Events: stable event name constants
    - LogCategory: logger name constants (app.access, app.app, etc.)
    - sanitize_body, sanitize_headers: PII masking for log payloads

Usage in services:
    import logging
    from common.logging import RequestContext, Events

    logger = logging.getLogger(__name__)

    def create_user(data: dict) -> User:
        user = ...
        logger.info(
            "User created",
            extra={
                "event": Events.USER_CREATED,
                "entity_type": "user",
                "entity_id": str(user.id),
            },
        )
        return user
"""

from common.logging.constants import Events, LogCategory
from common.logging.context import RequestContext
from common.logging.sanitizers import (
    body_summary,
    sanitize_body,
    sanitize_headers,
    sanitize_query_params,
)

__all__ = [
    "Events",
    "LogCategory",
    "RequestContext",
    "body_summary",
    "sanitize_body",
    "sanitize_headers",
    "sanitize_query_params",
]
