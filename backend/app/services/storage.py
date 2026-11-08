"""Pluggable Storage Service abstraction for file uploads (resumes).

Provides an abstract interface and a local file storage implementation.
Designed to be swapped seamlessly with AWS S3, Google Cloud Storage, or Azure Blob Storage.
"""

from abc import ABC, abstractmethod
import os
from pathlib import Path
from typing import Optional, Tuple
import uuid
from fastapi import HTTPException, status
from app.core.config import settings

MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {"application/pdf"}
PDF_MAGIC_BYTES = b"%PDF-"


class StorageService(ABC):
    """Abstract base class for resume file storage."""

    @abstractmethod
    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
        content_type: str,
    ) -> Tuple[str, str, int]:
        """Save file bytes and return (stored_filename, relative_file_path, file_size_bytes)."""
        pass

    @abstractmethod
    def get_file_path(self, stored_filename: str) -> Optional[Path]:
        """Return the absolute path on disk for secure streaming, or None if not found."""
        pass

    @abstractmethod
    def delete_file(self, stored_filename: str) -> bool:
        """Delete stored file. Return True if deleted, False if not found."""
        pass

    @abstractmethod
    def file_exists(self, stored_filename: str) -> bool:
        """Check if stored file exists."""
        pass


class LocalStorageService(StorageService):
    """Local filesystem storage abstraction.

    Keeps files private in an unexposed directory (not served directly as static files).
    Files can only be fetched via authenticated streaming endpoints.
    """

    def __init__(self, base_directory: Optional[Path] = None):
        if base_directory is None:
            # Use configured directory from settings, resolved relative to backend base
            backend_root = Path(__file__).resolve().parent.parent.parent
            self.base_dir = (backend_root / settings.RESUME_STORAGE_DIR).resolve()
        else:
            self.base_dir = Path(base_directory).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file_content: bytes, original_filename: str, content_type: str) -> None:
        """Validate file size, extension, MIME type, and PDF magic bytes."""
        if len(file_content) > MAX_RESUME_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {MAX_RESUME_SIZE_BYTES // (1024 * 1024)} MB.",
            )

        if not original_filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only PDF files (.pdf) are supported.",
            )

        # Check content type if supplied
        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid MIME type '{content_type}'. Must be application/pdf.",
            )

        # Magic bytes check for PDF
        if not file_content.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content header is not a valid PDF document.",
            )

    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
        content_type: str,
    ) -> Tuple[str, str, int]:
        """Validate and write file to secure local disk."""
        self.validate_file(file_content, original_filename, content_type)

        # Generate unguessable UUID filename
        stored_filename = f"{uuid.uuid4().hex}.pdf"
        target_path = self.base_dir / stored_filename

        with open(target_path, "wb") as f:
            f.write(file_content)

        relative_path = f"uploads/resumes/{stored_filename}"
        return stored_filename, relative_path, len(file_content)

    def get_file_path(self, stored_filename: str) -> Optional[Path]:
        """Return the absolute Path if file exists and is within base_dir (prevent path traversal)."""
        # Sanitize filename: strip any directory components
        safe_name = Path(stored_filename).name
        target_path = (self.base_dir / safe_name).resolve()

        # Prevent directory traversal attacks
        if not str(target_path).startswith(str(self.base_dir.resolve())):
            return None

        if target_path.is_file():
            return target_path
        return None

    def delete_file(self, stored_filename: str) -> bool:
        """Delete file if it exists."""
        target_path = self.get_file_path(stored_filename)
        if target_path and target_path.exists():
            try:
                target_path.unlink()
                return True
            except OSError:
                return False
        return False

    def file_exists(self, stored_filename: str) -> bool:
        path = self.get_file_path(stored_filename)
        return path is not None and path.exists()


class S3StorageService(StorageService):
    """Production S3-compatible private object storage service (AWS S3, Cloudflare R2, MinIO).

    Resumes are stored privately with zero public bucket policies or public URLs.
    Downloads stream securely through the authenticated backend API.
    """

    def __init__(self):
        self.bucket = settings.S3_BUCKET_NAME
        self.client = None
        try:
            import boto3
            session_kwargs = {}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                session_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                session_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            if settings.S3_REGION:
                session_kwargs["region_name"] = settings.S3_REGION

            client_kwargs = {}
            if settings.S3_ENDPOINT_URL:
                client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

            self.client = boto3.client("s3", **session_kwargs, **client_kwargs)
        except Exception:
            # Fallback if boto3 is not configured
            self.client = None

    def validate_file(self, file_content: bytes, original_filename: str, content_type: str) -> None:
        """Validate file size, extension, MIME type, and PDF magic bytes."""
        if len(file_content) > MAX_RESUME_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {MAX_RESUME_SIZE_BYTES // (1024 * 1024)} MB.",
            )

        if not original_filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only PDF files (.pdf) are supported.",
            )

        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid MIME type '{content_type}'. Must be application/pdf.",
            )

        if not file_content.startswith(PDF_MAGIC_BYTES):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content header is not a valid PDF document.",
            )

    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
        content_type: str,
    ) -> Tuple[str, str, int]:
        self.validate_file(file_content, original_filename, content_type)
        stored_filename = f"{uuid.uuid4().hex}.pdf"
        s3_key = f"resumes/{stored_filename}"

        if self.client and self.bucket:
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_content,
                ContentType="application/pdf",
                ServerSideEncryption="AES256",
            )
        return stored_filename, s3_key, len(file_content)

    def get_file_path(self, stored_filename: str) -> Optional[Path]:
        """In S3 mode, temporary cached stream or None."""
        return None

    def delete_file(self, stored_filename: str) -> bool:
        if self.client and self.bucket:
            try:
                self.client.delete_object(
                    Bucket=self.bucket,
                    Key=f"resumes/{stored_filename}",
                )
                return True
            except Exception:
                return False
        return False

    def file_exists(self, stored_filename: str) -> bool:
        if self.client and self.bucket:
            try:
                self.client.head_object(
                    Bucket=self.bucket,
                    Key=f"resumes/{stored_filename}",
                )
                return True
            except Exception:
                return False
        return False


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Dependency provider for storage service based on configured environment."""
    global _storage_service
    if _storage_service is None:
        if settings.STORAGE_BACKEND == "s3" and settings.S3_BUCKET_NAME:
            _storage_service = S3StorageService()
        else:
            _storage_service = LocalStorageService()
    return _storage_service
