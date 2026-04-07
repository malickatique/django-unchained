"""
Integration tests for upload API endpoints.

Tests the full HTTP request → view → service → DB round-trip.
Auth is not yet wired up — all tests use an authenticated client
via force_authenticate so the service layer gets a real user.
"""
import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from apps.uploads.models import Upload, UploadStatus
from apps.uploads.tests.factories import UploadFactory
from apps.users.models import Organisation, OrganisationStatus, User, UserType


@pytest.fixture
def organisation(db):
    return Organisation.objects.create(
        name="Test Bank",
        legal_name="Test Bank LLC",
        status=OrganisationStatus.ACTIVE,
    )


@pytest.fixture
def customer_user(organisation):
    return User.objects.create_user(
        email="customer@example.com",
        password="TestPass123!",
        organisation=organisation,
        user_type=UserType.CUSTOMER,
    )


@pytest.fixture
def api_client(customer_user):
    """Authenticated client — force_authenticate so service gets a real user."""
    client = APIClient()
    client.force_authenticate(user=customer_user)
    return client


# ---------------------------------------------------------------------------
# POST /api/v1/me/uploads/initiate
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUploadInitiateView:

    def test_initiate_returns_201_with_upload_id(self, api_client):
        response = api_client.post(
            "/api/v1/me/uploads/initiate",
            data={
                "filename": "emirates-front.jpg",
                "content_type": "image/jpeg",
                "category": "KYC_DOCUMENT",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "upload_id" in response.data
        assert response.data["status"] == "PENDING"
        assert response.data["original_filename"] == "emirates-front.jpg"
        assert response.data["content_type"] == "image/jpeg"
        assert response.data["category"] == "KYC_DOCUMENT"

    def test_initiate_creates_upload_record_in_db(self, api_client):
        response = api_client.post(
            "/api/v1/me/uploads/initiate",
            data={
                "filename": "passport.pdf",
                "content_type": "application/pdf",
                "category": "KYC_DOCUMENT",
            },
            format="json",
        )

        upload = Upload.objects.get(id=response.data["upload_id"])
        assert upload.status == UploadStatus.PENDING
        assert upload.original_filename == "passport.pdf"

    def test_initiate_rejects_invalid_content_type(self, api_client):
        response = api_client.post(
            "/api/v1/me/uploads/initiate",
            data={
                "filename": "virus.exe",
                "content_type": "application/x-executable",
                "category": "KYC_DOCUMENT",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_initiate_rejects_missing_fields(self, api_client):
        response = api_client.post(
            "/api/v1/me/uploads/initiate",
            data={},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "filename" in response.data
        assert "content_type" in response.data
        assert "category" in response.data


# ---------------------------------------------------------------------------
# POST /api/v1/me/uploads/{upload_id}/complete
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUploadCompleteView:

    def test_complete_returns_200_with_uploaded_status(
        self, api_client, customer_user
    ):
        upload = UploadFactory(
            uploaded_by_user_id=customer_user.id,
            organisation_id=customer_user.organisation_id,
            status=UploadStatus.PENDING,
        )
        file = SimpleUploadedFile(
            "test.jpg", b"fake image bytes", content_type="image/jpeg"
        )

        response = api_client.post(
            f"/api/v1/me/uploads/{upload.id}/complete",
            data={"file": file},
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["upload_id"] == str(upload.id)
        assert response.data["status"] == "UPLOADED"
        assert response.data["size_bytes"] == len(b"fake image bytes")

    def test_complete_persists_file_to_storage(
        self, api_client, customer_user, settings
    ):
        upload = UploadFactory(
            uploaded_by_user_id=customer_user.id,
            organisation_id=customer_user.organisation_id,
            status=UploadStatus.PENDING,
        )
        file = SimpleUploadedFile(
            "doc.pdf", b"pdf content", content_type="application/pdf"
        )

        api_client.post(
            f"/api/v1/me/uploads/{upload.id}/complete",
            data={"file": file},
            format="multipart",
        )

        upload.refresh_from_db()
        assert upload.storage_path != ""
        assert upload.file_hash_sha256 != ""

    def test_complete_rejects_missing_file(self, api_client, customer_user):
        upload = UploadFactory(
            uploaded_by_user_id=customer_user.id,
            status=UploadStatus.PENDING,
        )

        response = api_client.post(
            f"/api/v1/me/uploads/{upload.id}/complete",
            data={},
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "file" in response.data

    def test_complete_rejects_already_uploaded(
        self, api_client, customer_user
    ):
        upload = UploadFactory(
            uploaded_by_user_id=customer_user.id,
            status=UploadStatus.UPLOADED,
        )
        file = SimpleUploadedFile(
            "test.jpg", b"content", content_type="image/jpeg"
        )

        response = api_client.post(
            f"/api/v1/me/uploads/{upload.id}/complete",
            data={"file": file},
            format="multipart",
        )

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_complete_rejects_other_users_upload(
        self, api_client, organisation
    ):
        other_user_id = uuid.uuid4()
        upload = UploadFactory(
            uploaded_by_user_id=other_user_id,
            status=UploadStatus.PENDING,
        )
        file = SimpleUploadedFile(
            "test.jpg", b"content", content_type="image/jpeg"
        )

        response = api_client.post(
            f"/api/v1/me/uploads/{upload.id}/complete",
            data={"file": file},
            format="multipart",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_complete_rejects_nonexistent_upload(self, api_client):
        fake_id = uuid.uuid4()
        file = SimpleUploadedFile(
            "test.jpg", b"content", content_type="image/jpeg"
        )

        response = api_client.post(
            f"/api/v1/me/uploads/{fake_id}/complete",
            data={"file": file},
            format="multipart",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
