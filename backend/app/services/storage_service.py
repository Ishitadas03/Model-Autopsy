"""Cloudflare R2 (S3-compatible) and local object storage service for experiment artifacts and datasets."""

import hashlib
import mimetypes
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

try:
    from app.core.config import settings
    from app.core.logging import get_logger
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UploadResult:
    """Standardized metadata returned after an upload operation."""
    key: str
    provider: str  # "r2" or "local"
    size_bytes: int
    sha256_hash: str
    content_type: str
    etag: Optional[str] = None
    url: Optional[str] = None


def compute_sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hexadecimal hash from bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_sha256_file(path: Path | str, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hexadecimal hash from a local file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


class StorageService:
    """Unified service for interacting with Cloudflare R2 / S3-compatible object storage

    with an observable, reliable local filesystem fallback.
    """

    def __init__(self):
        self.bucket_name = settings.R2_BUCKET_NAME
        self.account_id = settings.R2_ACCOUNT_ID
        self.access_key_id = settings.R2_ACCESS_KEY_ID
        self.secret_access_key = settings.R2_SECRET_ACCESS_KEY
        self.endpoint_url = settings.R2_ENDPOINT_URL or os.getenv("R2_ENDPOINT") or os.getenv("R2_ENDPOINT_URL")

        if not self.endpoint_url and self.account_id:
            self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"

        self._client = None

    def is_configured(self) -> bool:
        """Check if R2 credentials and bucket are configured."""
        if getattr(settings, "STORAGE_PROVIDER", "auto") == "local":
            return False
        return bool(
            self.endpoint_url
            and self.access_key_id
            and self.secret_access_key
            and self.bucket_name
        )

    @property
    def active_provider(self) -> str:
        """Return the active storage provider name ('r2' or 'local')."""
        return "r2" if self.is_configured() else "local"

    @property
    def client(self):
        """Lazy-loaded boto3 S3 client configured for Cloudflare R2 with explicit timeouts."""
        if not self.is_configured():
            return None

        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name="auto",
                config=Config(
                    signature_version="s3v4",
                    connect_timeout=5,
                    read_timeout=15,
                    retries={"max_attempts": 3, "mode": "standard"},
                ),
            )
        return self._client

    # -------------------------------------------------------------------------
    # Health / Connectivity Inspection
    # -------------------------------------------------------------------------

    def check_bucket_access(self) -> Dict[str, Any]:
        """Perform a live head-bucket check to verify credentials and accessibility."""
        if not self.is_configured():
            return {
                "configured": False,
                "accessible": False,
                "bucket_name": self.bucket_name,
                "active_provider": self.active_provider,
                "error": "R2 credentials or endpoint not configured",
            }

        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return {
                "configured": True,
                "accessible": True,
                "bucket_name": self.bucket_name,
                "active_provider": "r2",
                "error": None,
            }
        except (ClientError, BotoCoreError, Exception) as e:
            logger.error("R2 head_bucket check failed", bucket=self.bucket_name, error=str(e))
            return {
                "configured": True,
                "accessible": False,
                "bucket_name": self.bucket_name,
                "active_provider": "local",
                "error": str(e),
            }

    # -------------------------------------------------------------------------
    # Path Resolver for Local Fallback
    # -------------------------------------------------------------------------

    def get_local_path(self, object_key: str) -> Path:
        """Resolve an object key to a safe absolute local path."""
        # Sanitize object key to prevent directory traversal
        sanitized = object_key.strip("/\\")
        parts = [p for p in sanitized.split("/") if p and p != ".."]
        clean_key = Path(*parts)

        if str(clean_key).startswith("datasets"):
            rel_path = clean_key.relative_to("datasets") if len(clean_key.parts) > 1 else clean_key
            base_dir = getattr(settings, "DATASETS_BASE_DIR", None) or (
                settings.ML_ENGINE_PATH.parent / "data" / "datasets"
            )
            return (base_dir / rel_path).resolve()
        else:
            base_dir = settings.ARTIFACTS_BASE_DIR.resolve()
            return (base_dir / clean_key).resolve()

    # -------------------------------------------------------------------------
    # Direct R2 Operations
    # -------------------------------------------------------------------------

    def upload_file_to_r2(
        self,
        local_path: Path | str,
        object_key: str,
        content_type: Optional[str] = None,
    ) -> Optional[UploadResult]:
        """Upload a local file directly to R2 with checksum verification."""
        if not self.is_configured():
            return None

        path = Path(local_path)
        if not path.is_file():
            logger.error("Local file does not exist for R2 upload", path=str(path))
            return None

        if not content_type:
            content_type, _ = mimetypes.guess_type(str(path))
            content_type = content_type or "application/octet-stream"

        file_size = path.stat().st_size
        sha256_hash = compute_sha256_file(path)

        try:
            extra_args = {
                "ContentType": content_type,
                "Metadata": {"sha256": sha256_hash},
            }
            self.client.upload_file(
                Filename=str(path),
                Bucket=self.bucket_name,
                Key=object_key,
                ExtraArgs=extra_args,
            )
            logger.info("Uploaded artifact to R2", key=object_key, size=file_size, sha256=sha256_hash)
            return UploadResult(
                key=object_key,
                provider="r2",
                size_bytes=file_size,
                sha256_hash=sha256_hash,
                content_type=content_type,
            )
        except (ClientError, BotoCoreError, Exception) as e:
            logger.error("Failed to upload file to R2", key=object_key, error=str(e))
            return None

    def upload_bytes_to_r2(
        self,
        data: bytes,
        object_key: str,
        content_type: str = "application/octet-stream",
    ) -> Optional[UploadResult]:
        """Upload in-memory bytes directly to R2."""
        if not self.is_configured():
            return None

        sha256_hash = compute_sha256_bytes(data)
        file_size = len(data)

        try:
            response = self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=data,
                ContentType=content_type,
                Metadata={"sha256": sha256_hash},
            )
            etag = response.get("ETag", "").strip('"')
            logger.info("Uploaded bytes to R2", key=object_key, bytes=file_size, sha256=sha256_hash)
            return UploadResult(
                key=object_key,
                provider="r2",
                size_bytes=file_size,
                sha256_hash=sha256_hash,
                content_type=content_type,
                etag=etag,
            )
        except (ClientError, BotoCoreError, Exception) as e:
            logger.error("Failed to upload bytes to R2", key=object_key, error=str(e))
            return None

    def download_file_from_r2(self, object_key: str, destination_path: Path | str) -> bool:
        """Download an object from R2 to a local destination atomically."""
        if not self.is_configured():
            return False

        dest = Path(destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        temp_dest = dest.with_suffix(dest.suffix + f".tmp_{os.getpid()}")

        try:
            self.client.download_file(
                Bucket=self.bucket_name,
                Key=object_key,
                Filename=str(temp_dest),
            )
            # Atomic rename after full download
            if temp_dest.exists():
                temp_dest.replace(dest)
            logger.info("Downloaded artifact from R2 atomically", key=object_key, destination=str(dest))
            return True
        except (ClientError, BotoCoreError, Exception) as e:
            logger.error("Failed to download from R2", key=object_key, error=str(e))
            if temp_dest.exists():
                try:
                    temp_dest.unlink()
                except OSError:
                    pass
            return False

    def get_object_bytes_from_r2(self, object_key: str) -> Optional[bytes]:
        """Fetch bytes of an object directly from R2."""
        if not self.is_configured():
            return None

        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
            return response["Body"].read()
        except (ClientError, BotoCoreError, Exception) as e:
            logger.error("Failed to fetch object bytes from R2", key=object_key, error=str(e))
            return None

    def delete_object_from_r2(self, object_key: str) -> bool:
        """Delete an object from R2 bucket."""
        if not self.is_configured():
            return False

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
            logger.info("Deleted object from R2", key=object_key)
            return True
        except (ClientError, BotoCoreError, Exception) as e:
            logger.error("Failed to delete object from R2", key=object_key, error=str(e))
            return False

    def generate_presigned_url(
        self,
        object_key: str,
        expiration_seconds: int = 3600,
    ) -> Optional[str]:
        """Generate a short-lived signed download URL for an R2 object."""
        if not self.is_configured():
            return None

        try:
            url = self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expiration_seconds,
            )
            return url
        except (ClientError, BotoCoreError, Exception) as e:
            logger.error("Failed to generate presigned URL for R2", key=object_key, error=str(e))
            return None

    def object_exists_in_r2(self, object_key: str) -> bool:
        """Check whether an object key exists in R2."""
        if not self.is_configured():
            return False

        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except (ClientError, BotoCoreError, Exception):
            return False

    def get_object_metadata_from_r2(self, object_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve size, etag, and metadata of an object from R2."""
        if not self.is_configured():
            return None

        try:
            res = self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return {
                "key": object_key,
                "size_bytes": res.get("ContentLength", 0),
                "content_type": res.get("ContentType", "application/octet-stream"),
                "etag": res.get("ETag", "").strip('"'),
                "sha256": res.get("Metadata", {}).get("sha256"),
                "last_modified": res.get("LastModified").isoformat() if res.get("LastModified") else None,
            }
        except (ClientError, BotoCoreError, Exception):
            return None

    # -------------------------------------------------------------------------
    # Unified Storage Methods (R2 with Local Fallback)
    # -------------------------------------------------------------------------

    def store_file(
        self,
        local_path: Path | str,
        object_key: str,
        content_type: Optional[str] = None,
    ) -> UploadResult:
        """Store a file in R2 if configured; otherwise store in local fallback directory."""
        path = Path(local_path)
        if not path.is_file():
            raise FileNotFoundError(f"Local file does not exist: {local_path}")

        file_size = path.stat().st_size
        sha256_hash = compute_sha256_file(path)
        if not content_type:
            content_type, _ = mimetypes.guess_type(str(path))
            content_type = content_type or "application/octet-stream"

        if self.is_configured():
            result = self.upload_file_to_r2(path, object_key, content_type)
            if result:
                return result
            logger.warning("R2 upload failed; falling back to local storage", key=object_key)

        # Local storage fallback
        dest_path = self.get_local_path(object_key)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if path.resolve() != dest_path.resolve():
            shutil.copy2(path, dest_path)

        return UploadResult(
            key=object_key,
            provider="local",
            size_bytes=file_size,
            sha256_hash=sha256_hash,
            content_type=content_type,
            url=f"file://{dest_path}",
        )

    def store_bytes(
        self,
        data: bytes,
        object_key: str,
        content_type: str = "application/octet-stream",
    ) -> UploadResult:
        """Store in-memory bytes in R2 if configured; otherwise in local fallback directory."""
        sha256_hash = compute_sha256_bytes(data)
        file_size = len(data)

        if self.is_configured():
            result = self.upload_bytes_to_r2(data, object_key, content_type)
            if result:
                return result
            logger.warning("R2 bytes upload failed; falling back to local storage", key=object_key)

        # Local storage fallback
        dest_path = self.get_local_path(object_key)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        temp_dest = dest_path.with_suffix(dest_path.suffix + f".tmp_{os.getpid()}")
        with open(temp_dest, "wb") as f:
            f.write(data)
        temp_dest.replace(dest_path)

        return UploadResult(
            key=object_key,
            provider="local",
            size_bytes=file_size,
            sha256_hash=sha256_hash,
            content_type=content_type,
            url=f"file://{dest_path}",
        )

    def retrieve_file(self, object_key: str, destination_path: Path | str) -> bool:
        """Retrieve a file from R2 or local fallback to a destination path."""
        # 1. Try R2 if configured
        if self.is_configured():
            if self.download_file_from_r2(object_key, destination_path):
                return True

        # 2. Try local fallback
        local_src = self.get_local_path(object_key)
        if local_src.exists() and local_src.is_file():
            dest = Path(destination_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if local_src.resolve() != dest.resolve():
                shutil.copy2(local_src, dest)
            return True

        return False

    def retrieve_bytes(self, object_key: str) -> Optional[bytes]:
        """Retrieve bytes from R2 or local storage."""
        if self.is_configured():
            data = self.get_object_bytes_from_r2(object_key)
            if data is not None:
                return data

        local_src = self.get_local_path(object_key)
        if local_src.exists() and local_src.is_file():
            try:
                with open(local_src, "rb") as f:
                    return f.read()
            except OSError as e:
                logger.error("Failed to read local fallback file", path=str(local_src), error=str(e))
                return None

        return None

    def object_exists(self, object_key: str) -> bool:
        """Check if an object exists in either R2 or local storage."""
        if self.is_configured():
            if self.object_exists_in_r2(object_key):
                return True

        local_src = self.get_local_path(object_key)
        return local_src.exists() and local_src.is_file()

    def delete_object(self, object_key: str) -> bool:
        """Delete an object from both R2 and local storage."""
        deleted_r2 = False
        if self.is_configured():
            deleted_r2 = self.delete_object_from_r2(object_key)

        deleted_local = False
        local_src = self.get_local_path(object_key)
        if local_src.exists() and local_src.is_file():
            try:
                local_src.unlink()
                deleted_local = True
            except OSError:
                pass

        return deleted_r2 or deleted_local

    def get_object_metadata(self, object_key: str) -> Optional[Dict[str, Any]]:
        """Get metadata from R2 or local file."""
        if self.is_configured():
            meta = self.get_object_metadata_from_r2(object_key)
            if meta:
                meta["provider"] = "r2"
                return meta

        local_src = self.get_local_path(object_key)
        if local_src.exists() and local_src.is_file():
            content_type, _ = mimetypes.guess_type(str(local_src))
            sha256 = compute_sha256_file(local_src)
            stat = local_src.stat()
            return {
                "key": object_key,
                "provider": "local",
                "size_bytes": stat.st_size,
                "content_type": content_type or "application/octet-stream",
                "etag": None,
                "sha256": sha256,
                "last_modified": stat.st_mtime,
            }

        return None

    # Legacy compatibility methods
    def upload_file(self, local_path: Path | str, object_key: str, content_type: Optional[str] = None) -> bool:
        return bool(self.store_file(local_path, object_key, content_type))

    def upload_bytes(self, data: bytes, object_key: str, content_type: str = "application/octet-stream") -> bool:
        return bool(self.store_bytes(data, object_key, content_type))

    def download_file(self, object_key: str, destination_path: Path | str) -> bool:
        return self.retrieve_file(object_key, destination_path)

    def get_object_bytes(self, object_key: str) -> Optional[bytes]:
        return self.retrieve_bytes(object_key)

    def list_objects(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List objects in R2 with fallback to local files."""
        if self.is_configured():
            try:
                response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
                contents = response.get("Contents", [])
                return [
                    {
                        "key": item["Key"],
                        "size": item["Size"],
                        "last_modified": item["LastModified"].isoformat(),
                        "provider": "r2",
                    }
                    for item in contents
                ]
            except (ClientError, BotoCoreError) as e:
                logger.error("Failed to list R2 objects", prefix=prefix, error=str(e))

        # Local fallback listing
        results = []
        base = settings.ARTIFACTS_BASE_DIR
        target_dir = base / prefix if prefix else base
        if target_dir.exists() and target_dir.is_dir():
            for p in target_dir.rglob("*"):
                if p.is_file():
                    rel_key = str(p.relative_to(base)).replace("\\", "/")
                    results.append({
                        "key": rel_key,
                        "size": p.stat().st_size,
                        "last_modified": p.stat().st_mtime,
                        "provider": "local",
                    })
        return results


# Global singleton instance
storage_service = StorageService()
