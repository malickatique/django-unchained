import uuid

import factory

from apps.uploads.models import (
    Upload,
    UploadCategory,
    UploadOwnerType,
    UploadStatus,
    StorageProvider,
    VirusScanStatus,
)


class UploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    organisation_id = factory.LazyFunction(uuid.uuid4)
    owner_type = UploadOwnerType.USER
    owner_id = factory.LazyFunction(uuid.uuid4)
    uploaded_by_user_id = factory.LazyFunction(uuid.uuid4)

    name = "test-file.jpg"
    original_filename = "test-file.jpg"
    content_type = "image/jpeg"
    extension = "jpg"
    size_bytes = 1024
    file_hash_sha256 = "abc123"

    storage_provider = StorageProvider.LOCAL
    storage_bucket = ""
    storage_path = "uploads/test/test-file.jpg"

    category = UploadCategory.KYC_DOCUMENT
    status = UploadStatus.PENDING
    virus_scan_status = VirusScanStatus.PENDING
