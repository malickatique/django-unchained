"""
Central exception handler for DRF — the @ControllerAdvice equivalent.

Registered in settings via:
    REST_FRAMEWORK = {
        "EXCEPTION_HANDLER": "common.exceptions.handler.api_exception_handler",
    }

Responsibilities:
    1. Catch our domain exceptions (BaseAPIException subclasses).
    2. Normalise DRF's built-in exceptions into our error envelope.
    3. Catch unhandled exceptions and return a safe SYSTEM_ERROR response.
    4. Strip debug details (exception_class, message, traceback) in production.
    5. Log full details server-side for every 5xx error.
"""

import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response

from common.exceptions.base import BaseAPIException
from common.exceptions.codes import ErrorCode, HTTP_STATUS_TO_ERROR_CODE
from common.logging.constants import Events, LogCategory

logger = logging.getLogger("common.exceptions.handler")
error_logger = logging.getLogger(LogCategory.ERROR)
security_logger = logging.getLogger(LogCategory.SECURITY)


# ── Public entry point ───────────────────────────────────────────────


def api_exception_handler(exc: Exception, context: dict) -> Response:
    """
    Single entry point wired into REST_FRAMEWORK["EXCEPTION_HANDLER"].

    Dispatches to specialised handlers based on exception type, then
    formats everything into the standard error envelope.
    """

    # 1. Our domain exceptions — highest priority
    if isinstance(exc, BaseAPIException):
        return _handle_domain_exception(exc)

    # 2. DRF ValidationError — field-level errors from serializers
    if isinstance(exc, DRFValidationError):
        return _handle_drf_validation_error(exc)

    # 3. Django ValidationError (raised in model.clean(), etc.)
    if isinstance(exc, DjangoValidationError):
        return _handle_django_validation_error(exc)

    # 4. DRF built-in exceptions (auth, permission, not found, throttle, etc.)
    if isinstance(exc, APIException):
        return _handle_drf_api_exception(exc)

    # 5. Django's Http404 (from get_object_or_404, URL resolver, etc.)
    if isinstance(exc, Http404):
        return _build_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message="The requested resource was not found.",
            error_code=ErrorCode.NOT_FOUND,
        )

    # 6. Django's PermissionDenied
    if isinstance(exc, DjangoPermissionDenied):
        return _build_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            message="You do not have permission to perform this action.",
            error_code=ErrorCode.PERMISSION_DENIED,
        )

    # 7. Unhandled / unexpected — SYSTEM_ERROR
    return _handle_unhandled_exception(exc, context)


# ── Specialised handlers ─────────────────────────────────────────────


def _handle_domain_exception(exc: BaseAPIException) -> Response:
    """Handle our custom domain exceptions (BusinessException, etc.)."""
    log_extra = {
        "event": Events.ERROR_BUSINESS_RULE,
        "category": "error",
        "error_code": exc.error_code,
        "exception_class": exc.__class__.__name__,
        "status_code": exc.status_code,
    }

    if exc.status_code >= 500:
        error_logger.error(
            f"Domain exception: {exc.message}",
            extra=log_extra,
            exc_info=True,
        )
    elif exc.status_code in (401, 403):
        security_logger.warning(
            f"Auth/permission exception: {exc.message}",
            extra={**log_extra, "event": Events.PERMISSION_DENIED, "category": "security"},
        )
    else:
        logger.warning(
            f"Domain exception: {exc.message}",
            extra=log_extra,
        )

    return _build_error_response(
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
    )


def _handle_drf_validation_error(exc: DRFValidationError) -> Response:
    """
    Normalise DRF's ValidationError into the flat details[] format.

    DRF can produce several shapes:
        - {"field": ["msg"]}                     (serializer field errors)
        - {"non_field_errors": ["msg"]}          (cross-field errors)
        - ["msg"]                                (non-field shorthand)
        - "msg"                                  (single string)
    """
    details = _flatten_drf_errors(exc.detail)

    logger.info(
        "Validation error",
        extra={
            "event": Events.ERROR_VALIDATION,
            "category": "error",
            "error_code": ErrorCode.VALIDATION_ERROR,
            "validation_error_count": len(details),
        },
    )

    return _build_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Validation failed.",
        error_code=ErrorCode.VALIDATION_ERROR,
        details=details,
    )


def _handle_django_validation_error(exc: DjangoValidationError) -> Response:
    """
    Normalise Django's core ValidationError into the flat details[] format.

    Django's ValidationError can carry:
        - message_dict   {"field": ["msg"]}
        - messages        ["msg"]
        - message         "msg"
    """
    details: list[dict[str, Any]] = []

    if hasattr(exc, "message_dict"):
        for field, messages in exc.message_dict.items():
            error_type = "non_field" if field == "__all__" else "field"
            field_name = None if field == "__all__" else field
            for msg in messages:
                detail_item: dict[str, Any] = {
                    "type": error_type,
                    "code": "INVALID",
                    "message": str(msg),
                }
                if field_name:
                    detail_item["field"] = field_name
                details.append(detail_item)
    else:
        for msg in exc.messages:
            details.append({
                "type": "non_field",
                "code": "INVALID",
                "message": str(msg),
            })

    return _build_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Validation failed.",
        error_code=ErrorCode.VALIDATION_ERROR,
        details=details,
    )


def _handle_drf_api_exception(exc: APIException) -> Response:
    """Map DRF's built-in exceptions to our envelope."""
    status_code = exc.status_code
    error_code = HTTP_STATUS_TO_ERROR_CODE.get(status_code, ErrorCode.SYSTEM_ERROR)
    message = _extract_message(exc.detail)

    return _build_error_response(
        status_code=status_code,
        message=message,
        error_code=error_code,
    )


def _handle_unhandled_exception(exc: Exception, context: dict) -> Response:
    """
    Catch-all for unexpected exceptions — returns SYSTEM_ERROR.

    Always logs the full traceback server-side. In DEBUG mode, includes
    exception_class and message in the response for developer convenience.
    """
    view_name = str(context.get("view", "unknown"))

    error_logger.error(
        f"Unhandled exception in {view_name}: {exc}",
        extra={
            "event": Events.ERROR_UNHANDLED,
            "category": "error",
            "error_code": ErrorCode.SYSTEM_ERROR,
            "exception_class": exc.__class__.__name__,
            "view_name": view_name,
        },
        exc_info=True,
    )

    details: list[dict[str, Any]] = []
    if settings.DEBUG:
        details.append({
            "type": "system",
            "exception_class": exc.__class__.__name__,
            "message": str(exc),
        })

    return _build_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=(
            "An unexpected error occurred."
            if settings.DEBUG
            else "Something went wrong. Please try again later."
        ),
        error_code=ErrorCode.SYSTEM_ERROR,
        details=details,
    )


# ── Envelope builder ─────────────────────────────────────────────────


def _build_error_response(
    *,
    status_code: int,
    message: str,
    error_code: str,
    details: list[dict[str, Any]] | None = None,
) -> Response:
    """
    Construct the standard error envelope.

    Shape:
        {
            "success": false,
            "message": "...",
            "data": null,
            "meta": {},
            "errors": {
                "code": "VALIDATION_ERROR",
                "details": [...]
            }
        }
    """
    body = {
        "success": False,
        "message": message,
        "data": None,
        "meta": {},
        "errors": {
            "code": error_code,
            "details": details or [],
        },
    }
    return Response(body, status=status_code)


# ── Helpers ──────────────────────────────────────────────────────────


def _flatten_drf_errors(
    detail: Any,
    *,
    parent_field: str = "",
) -> list[dict[str, Any]]:
    """
    Recursively flatten DRF's error detail into a list of dicts.

    Handles nested serializers by using dot-notation for field paths:
        {"profile": {"phone": ["Required"]}}
        →  [{"type": "field", "field": "profile.phone", ...}]

    Handles list serializers by using bracket notation:
        [{"name": ["Required"]}, {}]
        →  [{"type": "field", "field": "0.name", ...}]
    """
    results: list[dict[str, Any]] = []

    if isinstance(detail, dict):
        for field, errors in detail.items():
            if field == "non_field_errors":
                for err in errors:
                    results.append({
                        "type": "non_field",
                        "code": _extract_error_code(err),
                        "message": str(err),
                    })
            else:
                full_path = f"{parent_field}.{field}" if parent_field else field
                if (
                    isinstance(errors, list)
                    and errors
                    and isinstance(errors[0], dict)
                ):
                    # Nested serializer (list of dicts)
                    for i, nested in enumerate(errors):
                        results.extend(
                            _flatten_drf_errors(nested, parent_field=f"{full_path}.{i}")
                        )
                elif isinstance(errors, dict):
                    # Single nested serializer
                    results.extend(_flatten_drf_errors(errors, parent_field=full_path))
                else:
                    for err in (errors if isinstance(errors, list) else [errors]):
                        results.append({
                            "type": "field",
                            "field": full_path,
                            "code": _extract_error_code(err),
                            "message": str(err),
                        })

    elif isinstance(detail, list):
        for item in detail:
            if isinstance(item, dict):
                results.extend(_flatten_drf_errors(item, parent_field=parent_field))
            else:
                results.append({
                    "type": "non_field",
                    "code": _extract_error_code(item),
                    "message": str(item),
                })

    elif isinstance(detail, str):
        results.append({
            "type": "non_field",
            "code": "INVALID",
            "message": detail,
        })

    return results


def _extract_error_code(error_detail: Any) -> str:
    """
    Pull the .code attribute from a DRF ErrorDetail object.

    DRF attaches codes like "required", "invalid", "blank", etc. to each
    ErrorDetail string. We uppercase them for consistency with our ErrorCode enum.
    """
    code = getattr(error_detail, "code", None)
    if code:
        return str(code).upper()
    return "INVALID"


def _extract_message(detail: Any) -> str:
    """Convert DRF's detail (string, list, or dict) into a single message string."""
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return str(detail[0]) if detail else "An error occurred."
    if isinstance(detail, dict):
        for key in ("detail", "message", "non_field_errors"):
            if key in detail:
                val = detail[key]
                if isinstance(val, list):
                    return str(val[0]) if val else "An error occurred."
                return str(val)
        first = next(iter(detail.values()), None)
        if isinstance(first, list) and first:
            return str(first[0])
        if first:
            return str(first)
    return "An error occurred."
