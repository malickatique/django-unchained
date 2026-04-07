"""
Storage backend abstraction for file uploads.

Currently supports LOCAL storage only. S3/GCS/Azure backends will be added
as separate classes behind the same interface.

The storage layer handles physical file operations (write, read, delete, exists).
It does NOT handle metadata (that's the Upload model's job via upload_service.py).
"""
import hashlib
from pathlib import Path
from typing import Protocol

from django.conf import settings


class StorageBackend(Protocol):
    """Interface that all storage backends must implement."""

    def save(self, path: str, content: bytes) -> str:
        """Save content to the given path. Return the final storage path."""
        ...

    def read(self, path: str) -> bytes:
        """Read and return file content from path."""
        ...

    def delete(self, path: str) -> None:
        """Delete file at path. No-op if file does not exist."""
        ...

    def exists(self, path: str) -> bool:
        """Check if file exists at path."""
        ...

    def url(self, path: str) -> str:
        """Return a URL to access the file."""
        ...


class LocalStorageBackend:
    """
    Stores files on the local filesystem under settings.UPLOAD_STORAGE_ROOT.

    File layout: {storage_root}/{path}
    """

    def __init__(self) -> None:
        self.root = Path(
            getattr(settings, "UPLOAD_STORAGE_ROOT", settings.BASE_DIR / "storage")
        )

    def save(self, path: str, content: bytes) -> str:
        full_path = self.root / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return path

    def read(self, path: str) -> bytes:
        full_path = self.root / path
        return full_path.read_bytes()

    def delete(self, path: str) -> None:
        full_path = self.root / path
        if full_path.exists():
            full_path.unlink()

    def exists(self, path: str) -> bool:
        return (self.root / path).exists()

    def url(self, path: str) -> str:
        base_url = getattr(settings, "UPLOAD_STORAGE_URL", "/storage/")
        return f"{base_url}{path}"


def get_storage_backend() -> LocalStorageBackend:
    """
    Factory function returning the active storage backend.

    When S3 support is added, this will read from settings.UPLOAD_STORAGE_PROVIDER
    and return the appropriate backend.
    """
    return LocalStorageBackend()


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()
