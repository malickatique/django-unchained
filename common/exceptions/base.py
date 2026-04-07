"""
Domain exception hierarchy for the API contract layer.

Services raise these exceptions with a human-readable message and an
optional error code. The central exception handler (handler.py) catches
them and formats the response envelope.

Spring Boot analogy:
    BaseAPIException    ≈  ResponseStatusException
    ValidationException ≈  MethodArgumentNotValidException (field-level)
    BusinessException   ≈  custom RuntimeException subclass
    NotFoundException   ≈  ResponseStatusException(NOT_FOUND)

Usage in services:
    from common.exceptions import BusinessException, NotFoundException
    from common.exceptions import ErrorCode

    def submit_order(order_id: str, user) -> Order:
        order = Order.objects.filter(id=order_id, user=user).first()
        if not order:
            raise NotFoundException("Order not found.")
        if order.status != "DRAFT":
            raise BusinessException(
                message="Only draft orders can be submitted.",
                error_code=ErrorCode.INVALID_STATE_TRANSITION,
            )
"""

from typing import Any

from common.exceptions.codes import ErrorCode


class BaseAPIException(Exception):
    """
    Abstract base for all domain exceptions.

    Subclasses set `default_status_code` and `default_error_code`.
    Services override `message` and optionally `error_code` per instance.
    """

    default_status_code: int = 500
    default_error_code: str = ErrorCode.SYSTEM_ERROR

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        status_code: int | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.message = message or self._default_message()
        self.error_code = error_code or self.default_error_code
        self.status_code = status_code or self.default_status_code
        self.details = details or []
        super().__init__(self.message)

    def _default_message(self) -> str:
        return "An error occurred."


class ValidationException(BaseAPIException):
    """
    Field-level validation failure.

    Used when serializer / input validation fails and the consumer
    needs to map errors back to specific form fields.

    `details` should be a list of dicts with:
        {"type": "field", "field": "email", "code": "REQUIRED", "message": "..."}
    """

    default_status_code = 400
    default_error_code = ErrorCode.VALIDATION_ERROR

    def _default_message(self) -> str:
        return "Validation failed."


class BusinessException(BaseAPIException):
    """
    Business rule violation — request is syntactically valid but violates
    a domain constraint not tied to a single input field.

    Use INVALID_STATE_TRANSITION for FSM violations,
    BUSINESS_RULE_VIOLATION for general domain rules,
    CONFLICT for duplicate/already-exists cases.
    """

    default_status_code = 400
    default_error_code = ErrorCode.BUSINESS_RULE_VIOLATION

    def _default_message(self) -> str:
        return "The request could not be processed."


class AuthenticationException(BaseAPIException):
    """
    Authentication failure — missing, invalid, or expired credentials.
    """

    default_status_code = 401
    default_error_code = ErrorCode.AUTHENTICATION_ERROR

    def _default_message(self) -> str:
        return "Authentication credentials were not provided."


class PermissionException(BaseAPIException):
    """
    Authorization failure — authenticated but not allowed.
    """

    default_status_code = 403
    default_error_code = ErrorCode.PERMISSION_DENIED

    def _default_message(self) -> str:
        return "You do not have permission to perform this action."


class NotFoundException(BaseAPIException):
    """
    Resource not found.

    Prefer this over Django's Http404 in service layer code so that
    the response envelope stays consistent.
    """

    default_status_code = 404
    default_error_code = ErrorCode.NOT_FOUND

    def _default_message(self) -> str:
        return "The requested resource was not found."


class ConflictException(BaseAPIException):
    """
    Duplicate resource or conflicting state.
    """

    default_status_code = 409
    default_error_code = ErrorCode.CONFLICT

    def _default_message(self) -> str:
        return "A conflicting resource already exists."


class ServiceUnavailableException(BaseAPIException):
    """
    Downstream dependency is unavailable (external API, queue, etc.).
    """

    default_status_code = 503
    default_error_code = ErrorCode.SERVICE_UNAVAILABLE

    def _default_message(self) -> str:
        return (
            "A required service is temporarily unavailable. "
            "Please try again later."
        )
