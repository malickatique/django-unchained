"""
Log formatters for structured output.

Two formatters:
    - JsonFormatter: Machine-readable JSON, one object per line.
      Used for file handlers (dev) and stdout (prod → ELK/Datadog).
    - ConsoleFormatter: Human-readable coloured text for local dev terminal.

Both formatters read extra fields from the LogRecord (injected by
RequestContextFilter) and include them in output.
"""

from __future__ import annotations

import json
import logging
import socket
import traceback
from datetime import datetime, timezone
from typing import Any

from common.logging.constants import SERVICE_NAME


# ── JSON Formatter ───────────────────────────────────────────────────


class JsonFormatter(logging.Formatter):
    """
    Formats each log record as a single-line JSON object.

    Output fields:
        - Universal: timestamp, level, logger, service, environment,
          version, hostname, process_id, event, message, category
        - Request-scoped: request_id, correlation_id, method, path, etc.
          (injected by RequestContextFilter)
        - Error: exception_class, stack_trace (for ERROR/CRITICAL)
        - Extra: any additional fields passed via logger.info(..., extra={})

    The formatter merges all sources into one flat JSON object.
    """

    # Fields that are part of the standard LogRecord and should NOT be
    # included in the JSON output (they're noise or already extracted).
    _SKIP_FIELDS: frozenset[str] = frozenset({
        "name", "msg", "args", "created", "relativeCreated",
        "thread", "threadName", "msecs", "pathname", "filename",
        "module", "funcName", "lineno", "exc_info", "exc_text",
        "stack_info", "levelname", "levelno", "message",
        "taskName", "process",
    })

    def __init__(self, environment: str = "development", version: str = "dev"):
        super().__init__()
        self._environment = environment
        self._version = version
        self._hostname = socket.gethostname()

    def format(self, record: logging.LogRecord) -> str:
        """Format a LogRecord as a JSON string."""
        # Build the base structure
        log_dict: dict[str, Any] = {
            "timestamp": self._format_timestamp(record),
            "level": record.levelname,
            "logger": record.name,
            "service": SERVICE_NAME,
            "environment": self._environment,
            "version": self._version,
            "hostname": self._hostname,
            "pid": record.process,
        }

        # Message — format with args if present
        log_dict["message"] = record.getMessage()

        # Merge extra fields from the record (injected by filters, or
        # passed via logger.info("msg", extra={...}))
        for key, value in record.__dict__.items():
            if key not in self._SKIP_FIELDS and key not in log_dict:
                log_dict[key] = value

        # Exception info
        if record.exc_info and record.exc_info[1] is not None:
            exc = record.exc_info[1]
            log_dict["exception_class"] = exc.__class__.__name__
            log_dict["stack_trace"] = self._format_exception(record.exc_info)

        # Stack info (for stack_info=True calls)
        if record.stack_info:
            log_dict["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(log_dict, default=str, ensure_ascii=False)

    @staticmethod
    def _format_timestamp(record: logging.LogRecord) -> str:
        """ISO 8601 with timezone."""
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat()

    @staticmethod
    def _format_exception(exc_info: tuple) -> str:
        """Format exception traceback as a string."""
        return "".join(traceback.format_exception(*exc_info)).strip()


# ── Console Formatter ────────────────────────────────────────────────


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable coloured formatter for local development.

    Format:
        [2026-04-04 14:23:01] INFO  app.access | http.request.received
        POST /api/v1/users/ | req=a1b2c3d4 | user=0196a3bc

    Colour codes:
        DEBUG    → dim grey
        INFO     → green
        WARNING  → yellow
        ERROR    → red
        CRITICAL → bold red
    """

    COLOURS = {
        "DEBUG": "\033[90m",      # dim grey
        "INFO": "\033[32m",       # green
        "WARNING": "\033[33m",    # yellow
        "ERROR": "\033[31m",      # red
        "CRITICAL": "\033[1;31m", # bold red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format a LogRecord as coloured human-readable text."""
        colour = self.COLOURS.get(record.levelname, "")
        reset = self.RESET

        # Timestamp
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        ts = dt.strftime("%Y-%m-%d %H:%M:%S")

        # Event name (from extra, if present)
        event = getattr(record, "event", "")
        event_str = f" | {event}" if event else ""

        # Core line
        line = (
            f"{colour}[{ts}] {record.levelname:<8}{reset}"
            f" {record.name}{event_str}"
        )

        # Message
        message = record.getMessage()
        if message:
            line += f"\n  {message}"

        # Key context fields (compact)
        context_parts = []
        for field in ("request_id", "auth_user_id", "method", "path",
                       "status_code", "duration_ms", "outcome"):
            value = getattr(record, field, None)
            if value is not None:
                # Shorten request_id / user_id for readability
                display = str(value)
                if field in ("request_id", "auth_user_id") and len(display) > 12:
                    display = display[:8]
                context_parts.append(f"{field}={display}")

        if context_parts:
            line += f"\n  {' | '.join(context_parts)}"

        # Exception
        if record.exc_info and record.exc_info[1] is not None:
            line += f"\n{colour}{self.formatException(record.exc_info)}{reset}"

        return line
