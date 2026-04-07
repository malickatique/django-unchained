"""
Upload service — business logic for file upload lifecycle.

Two-phase upload flow:
1. initiate_upload() — creates Upload record in PENDING, returns upload metadata.
2. complete_upload() — receives file content, persists to storage, updates record.

For local storage the client sends the file directly in the complete request.
When S3 is added, initiate will return a presigned URL and complete will
verify the file landed in S3 (no file content in the complete request).
"""
import uuid
from datetime import datetime
from pathlib import PurePosixPath
from typing import Optional

from django.utils import timezone

from apps.uploads.models import (
    Upload,
    UploadCategory,
    UploadOwnerType,
    UploadStatus,
    StorageProvider,
    VirusScanStatus,
)
from apps.uploads.services.storage import compute_file_hash, get_storage_backend
from apps.uploads.exceptions import ConflictError, InvalidStateError, NotFoundError


# ---------------------------------------------------------------------------
# Allowed file types — whitelist approach for banking
# ---------------------------------------------------------------------------

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "application/pdf",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _build_storage_path(
    organisation_id: uuid.UUID,
    upload_id: uuid.UUID,
    filename: str,
) -> str:
    """
    Build a deterministic, collision-free storage path.

    Layout: uploads/{org_id}/{YYYY}/{MM}/{upload_id}/{filename}
    """
    now = timezone.now()
    ext = PurePosixPath(filename).suffix.lower()
    safe_name = f"{upload_id}{ext}"
    return f"uploads/{organisation_id}/{now.year}/{now.month:02d}/{upload_id}/{safe_name}"


def _extract_extension(filename: str) -> str:
    """Extract lowercase file extension without the leading dot."""
    ext = PurePosixPath(filename).suffix.lower()
    return ext.lstrip(".")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _resolve_user_ids(user) -> tuple:
    """
    Extract user_id and organisation_id from the request user.

    Handles both authenticated Django users and anonymous users.
    When auth is not yet wired up, falls back to a placeholder org ID.
    """
    if user and getattr(user, "is_authenticated", False):
        return user.id, user.organisation_id
    # Anonymous / no auth — use placeholder values.
    # TODO: Remove this fallback when auth is wired up.
    _placeholder_org = uuid.UUID("00000000-0000-0000-0000-000000000000")
    _placeholder_user = uuid.UUID("00000000-0000-0000-0000-000000000000")
    return _placeholder_user, _placeholder_org


def initiate_upload(
    *,
    user,
    filename: str,
    content_type: str,
    category: str,
) -> Upload:
    """
    Phase 1: Create an Upload record in PENDING status.

    Validates content type and category. Returns the Upload instance
    with an ID the client uses to complete the upload.
    """
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ConflictError(
            detail=f"Content type '{content_type}' is not allowed. "
            f"Allowed types: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
            code="invalid_content_type",
        )

    if category not in UploadCategory.values:
        raise ConflictError(
            detail=f"Category '{category}' is not valid.",
            code="invalid_category",
        )

    user_id, organisation_id = _resolve_user_ids(user)

    upload = Upload(
        organisation_id=organisation_id,
        owner_type=UploadOwnerType.USER,
        owner_id=user_id,
        uploaded_by_user_id=user_id,
        name=filename,
        original_filename=filename,
        content_type=content_type,
        extension=_extract_extension(filename),
        size_bytes=0,
        file_hash_sha256="",
        storage_provider=StorageProvider.LOCAL,
        storage_bucket="",
        storage_path="",
        category=category,
        status=UploadStatus.PENDING,
        virus_scan_status=VirusScanStatus.PENDING,
    )
    upload.save()
    return upload


def complete_upload(
    *,
    upload_id: uuid.UUID,
    user,
    file_content: bytes,
) -> Upload:
    """
    Phase 2: Receive file content, persist to storage, update Upload record.

    Validates:
    - Upload exists and belongs to the user.
    - Upload is in PENDING status (not already completed).
    - File size is within limits.

    Returns the updated Upload instance with status=UPLOADED.
    """
    user_id, _ = _resolve_user_ids(user)
    upload = _get_user_upload(upload_id=upload_id, user_id=user_id)

    if upload.status != UploadStatus.PENDING:
        raise InvalidStateError(
            detail=(
                f"Upload is in '{upload.status}' status. "
                f"Only PENDING uploads can be completed."
            ),
            code="upload_not_pending",
        )

    size_bytes = len(file_content)
    if size_bytes == 0:
        raise ConflictError(
            detail="File content is empty.",
            code="empty_file",
        )

    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise ConflictError(
            detail=(
                f"File size ({size_bytes} bytes) exceeds maximum "
                f"allowed size ({MAX_FILE_SIZE_BYTES} bytes)."
            ),
            code="file_too_large",
        )

    # Persist file to storage
    storage = get_storage_backend()
    storage_path = _build_storage_path(
        organisation_id=upload.organisation_id,
        upload_id=upload.id,
        filename=upload.original_filename,
    )
    storage.save(storage_path, file_content)

    # Update record
    upload.storage_path = storage_path
    upload.size_bytes = size_bytes
    upload.file_hash_sha256 = compute_file_hash(file_content)
    upload.status = UploadStatus.UPLOADED
    upload.save()

    return upload


def get_upload(
    *,
    upload_id: uuid.UUID,
    user,
) -> Upload:
    """Retrieve a single upload belonging to the user."""
    user_id, _ = _resolve_user_ids(user)
    return _get_user_upload(upload_id=upload_id, user_id=user_id)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_user_upload(*, upload_id: uuid.UUID, user_id: uuid.UUID) -> Upload:
    """Fetch an upload scoped to the given user ID."""
    try:
        return Upload.objects.get(
            id=upload_id,
            uploaded_by_user_id=user_id,
        )
    except Upload.DoesNotExist:
        raise NotFoundError(
            detail="Upload not found.",
            code="upload_not_found",
        )
