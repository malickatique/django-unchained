"""
Exception package — re-exports for clean imports.

Usage:
    from common.exceptions import BusinessException, NotFoundException
    from common.exceptions import ErrorCode
    from common.exceptions import api_exception_handler
"""

from common.exceptions.base import (
    AuthenticationException,
    BaseAPIException,
    BusinessException,
    ConflictException,
    NotFoundException,
    PermissionException,
    ServiceUnavailableException,
    ValidationException,
)
from common.exceptions.codes import ErrorCode, HTTP_STATUS_TO_ERROR_CODE
from common.exceptions.handler import api_exception_handler

__all__ = [
    # Exception classes
    "BaseAPIException",
    "ValidationException",
    "BusinessException",
    "AuthenticationException",
    "PermissionException",
    "NotFoundException",
    "ConflictException",
    "ServiceUnavailableException",
    # Error codes
    "ErrorCode",
    "HTTP_STATUS_TO_ERROR_CODE",
    # Handler
    "api_exception_handler",
]
