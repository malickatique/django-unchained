from django.db import models

from common.mixins import UuidModel, AuditModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UploadOwnerType(models.TextChoices):
    USER = "USER", "User"
    KYC_CASE = "KYC_CASE", "KYC Case"
    BUSINESS = "BUSINESS", "Business"
    SYSTEM = "SYSTEM", "System"


class StorageProvider(models.TextChoices):
    LOCAL = "LOCAL", "Local"
    S3 = "S3", "S3"
    GCS = "GCS", "GCS"
    AZURE = "AZURE", "Azure"


class UploadCategory(models.TextChoices):
    PROFILE_PICTURE = "PROFILE_PICTURE", "Profile Picture"
    KYC_DOCUMENT = "KYC_DOCUMENT", "KYC Document"
    SELFIE = "SELFIE", "Selfie"
    PROOF_OF_ADDRESS = "PROOF_OF_ADDRESS", "Proof of Address"
    SALARY_CERTIFICATE = "SALARY_CERTIFICATE", "Salary Certificate"
    BANK_STATEMENT = "BANK_STATEMENT", "Bank Statement"
    TAX_RETURN = "TAX_RETURN", "Tax Return"
    TRADE_LICENCE = "TRADE_LICENCE", "Trade Licence"
    CONSENT = "CONSENT", "Consent"
    OTHER = "OTHER", "Other"


class UploadStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    UPLOADED = "UPLOADED", "Uploaded"
    SCANNED = "SCANNED", "Scanned"
    FAILED = "FAILED", "Failed"
    QUARANTINED = "QUARANTINED", "Quarantined"
    DELETED = "DELETED", "Deleted"


class VirusScanStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PASSED = "PASSED", "Passed"
    FAILED = "FAILED", "Failed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Upload(UuidModel, AuditModel):
    """
    Central file storage registry. All uploaded files across the platform
    are tracked here — KYC documents, profile pictures, salary certs, etc.

    Uses polymorphic ownership (owner_type + owner_id) to avoid tight FK
    coupling across apps. Same pattern as Laravel's morphTo().

    Spring Boot analogy: A generic @Entity FileMetadata with @Enumerated
    ownerType and UUID ownerId, rather than separate tables per entity.
    """
    # Polymorphic ownership
    organisation_id = models.UUIDField()
    owner_type = models.CharField(max_length=20, choices=UploadOwnerType.choices)
    owner_id = models.UUIDField()
    uploaded_by_user_id = models.UUIDField(blank=True, null=True)

    # File metadata
    name = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    extension = models.CharField(max_length=20, blank=True, default="")
    size_bytes = models.BigIntegerField()
    file_hash_sha256 = models.CharField(max_length=128)

    # Storage location
    storage_provider = models.CharField(
        max_length=10,
        choices=StorageProvider.choices,
    )
    storage_bucket = models.CharField(max_length=255, blank=True, default="")
    storage_path = models.CharField(max_length=1024)

    # Classification and status
    category = models.CharField(max_length=30, choices=UploadCategory.choices)
    status = models.CharField(
        max_length=20,
        choices=UploadStatus.choices,
        default=UploadStatus.PENDING,
    )

    # Security
    virus_scan_status = models.CharField(
        max_length=20,
        choices=VirusScanStatus.choices,
        default=VirusScanStatus.PENDING,
    )
    encrypted_at_rest = models.BooleanField(default=True)

    # Retention (regulatory: banking docs retained 5-10 years)
    retention_until = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "uploads"
        indexes = [
            models.Index(
                fields=["organisation_id", "owner_type", "owner_id"],
                name="idx_uploads_org_owner",
            ),
            models.Index(fields=["category"], name="idx_uploads_category"),
            models.Index(fields=["status"], name="idx_uploads_status"),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.category})"
