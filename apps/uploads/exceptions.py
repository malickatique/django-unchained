"""
Upload-specific exceptions.

These are local to the uploads app for now. When a common exception
strategy is established, they can be moved to common/exceptions.py
and these can become re-exports.
"""
from rest_framework import status
from rest_framework.exceptions import APIException


class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This operation conflicts with the current state."
    default_code = "conflict"


class NotFoundError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The requested resource was not found."
    default_code = "not_found"


class InvalidStateError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This operation is not allowed in the current state."
    default_code = "invalid_state"
