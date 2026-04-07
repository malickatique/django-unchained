"""
Tests for upload service layer.

Covers: initiate_upload, complete_upload, state guards, validation.
"""
import uuid
from unittest.mock import MagicMock

import pytest

from apps.uploads.models import Upload, UploadStatus
from apps.uploads.services.upload_service import (
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE_BYTES,
    complete_upload,
    initiate_upload,
)
from apps.uploads.tests.factories import UploadFactory
from apps.uploads.exceptions import ConflictError, InvalidStateError, NotFoundError


def _make_user(organisation_id=None):
    """Create a lightweight mock user for service calls."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.organisation_id = organisation_id or uuid.uuid4()
    return user


# ---------------------------------------------------------------------------
# initiate_upload
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInitiateUpload:

    def test_initiate_upload_creates_pending_record(self):
        user = _make_user()

        upload = initiate_upload(
            user=user,
            filename="emirates-front.jpg",
            content_type="image/jpeg",
            category="KYC_DOCUMENT",
        )

        assert isinstance(upload, Upload)
        assert upload.status == UploadStatus.PENDING
        assert upload.original_filename == "emirates-front.jpg"
        assert upload.content_type == "image/jpeg"
        assert upload.category == "KYC_DOCUMENT"
        assert upload.extension == "jpg"
        assert upload.uploaded_by_user_id == user.id
        assert upload.organisation_id == user.organisation_id
        assert upload.size_bytes == 0
        assert upload.file_hash_sha256 == ""

    def test_initiate_upload_rejects_disallowed_content_type(self):
        user = _make_user()

        with pytest.raises(ConflictError) as exc_info:
            initiate_upload(
                user=user,
                filename="malware.exe",
                content_type="application/x-executable",
                category="KYC_DOCUMENT",
            )

        assert "not allowed" in str(exc_info.value.detail)

    def test_initiate_upload_rejects_invalid_category(self):
        user = _make_user()

        with pytest.raises(ConflictError) as exc_info:
            initiate_upload(
                user=user,
                filename="test.jpg",
                content_type="image/jpeg",
                category="NONSENSE_CATEGORY",
            )

        assert "not valid" in str(exc_info.value.detail)

    def test_initiate_upload_accepts_all_allowed_content_types(self):
        user = _make_user()

        for ct in ALLOWED_CONTENT_TYPES:
            upload = initiate_upload(
                user=user,
                filename=f"test.{ct.split('/')[-1]}",
                content_type=ct,
                category="KYC_DOCUMENT",
            )
            assert upload.status == UploadStatus.PENDING

    def test_initiate_upload_extracts_extension_from_filename(self):
        user = _make_user()

        upload = initiate_upload(
            user=user,
            filename="Document.PDF",
            content_type="application/pdf",
            category="KYC_DOCUMENT",
        )
        assert upload.extension == "pdf"


# ---------------------------------------------------------------------------
# complete_upload
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCompleteUpload:

    def test_complete_upload_persists_file_and_updates_record(self):
        user = _make_user()
        upload = UploadFactory(
            uploaded_by_user_id=user.id,
            organisation_id=user.organisation_id,
            status=UploadStatus.PENDING,
        )
        file_content = b"fake jpeg content here"

        result = complete_upload(
            upload_id=upload.id,
            user=user,
            file_content=file_content,
        )

        assert result.status == UploadStatus.UPLOADED
        assert result.size_bytes == len(file_content)
        assert result.file_hash_sha256 != ""
        assert result.storage_path != ""

    def test_complete_upload_rejects_already_completed(self):
        user = _make_user()
        upload = UploadFactory(
            uploaded_by_user_id=user.id,
            status=UploadStatus.UPLOADED,
        )

        with pytest.raises(InvalidStateError) as exc_info:
            complete_upload(
                upload_id=upload.id,
                user=user,
                file_content=b"some content",
            )

        assert "PENDING" in str(exc_info.value.detail)

    def test_complete_upload_rejects_empty_file(self):
        user = _make_user()
        upload = UploadFactory(
            uploaded_by_user_id=user.id,
            status=UploadStatus.PENDING,
        )

        with pytest.raises(ConflictError) as exc_info:
            complete_upload(
                upload_id=upload.id,
                user=user,
                file_content=b"",
            )

        assert "empty" in str(exc_info.value.detail)

    def test_complete_upload_rejects_oversized_file(self):
        user = _make_user()
        upload = UploadFactory(
            uploaded_by_user_id=user.id,
            status=UploadStatus.PENDING,
        )
        oversized = b"x" * (MAX_FILE_SIZE_BYTES + 1)

        with pytest.raises(ConflictError) as exc_info:
            complete_upload(
                upload_id=upload.id,
                user=user,
                file_content=oversized,
            )

        assert "exceeds" in str(exc_info.value.detail)

    def test_complete_upload_rejects_wrong_user(self):
        owner = _make_user()
        other_user = _make_user()
        upload = UploadFactory(
            uploaded_by_user_id=owner.id,
            status=UploadStatus.PENDING,
        )

        with pytest.raises(NotFoundError):
            complete_upload(
                upload_id=upload.id,
                user=other_user,
                file_content=b"some content",
            )

    def test_complete_upload_rejects_nonexistent_id(self):
        user = _make_user()

        with pytest.raises(NotFoundError):
            complete_upload(
                upload_id=uuid.uuid4(),
                user=user,
                file_content=b"some content",
            )
