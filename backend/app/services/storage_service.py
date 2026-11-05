"""Cloudflare R2 (S3-compatible) object storage service for experiment artifacts and datasets."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import mimetypes

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from backend.app.core.config import settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Service for interacting with Cloudflare R2 / S3-compatible object storage."""

    def __init__(self):
        self.bucket_name = settings.R2_BUCKET_NAME
        self.account_id = settings.R2_ACCOUNT_ID
        self.access_key_id = settings.R2_ACCESS_KEY_ID
        self.secret_access_key = settings.R2_SECRET_ACCESS_KEY
        self.endpoint_url = settings.R2_ENDPOINT_URL

        if not self.endpoint_url and self.account_id:
            self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"

        self._client = None

    def is_configured(self) -> bool:
        """Check if R2 credentials and bucket are configured."""
        return bool(
            self.endpoint_url
            and self.access_key_id
            and self.secret_access_key
            and self.bucket_name
        )

    @property
    def client(self):
        """Lazy-loaded boto3 S3 client configured for Cloudflare R2."""
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
                    retries={"max_attempts": 3, "mode": "standard"},
                ),
            )
        return self._client

    def upload_file(
        self,
        local_path: Path | str,
        object_key: str,
        content_type: Optional[str] = None,
    ) -> bool:
        """Upload a local file to R2 bucket."""
        if not self.is_configured():
            logger.debug("R2 storage not configured; skipping upload.", key=object_key)
            return False

        path = Path(local_path)
        if not path.is_file():
            logger.error("Local file does not exist for R2 upload", path=str(path))
            return False

        if not content_type:
            content_type, _ = mimetypes.guess_type(str(path))
            content_type = content_type or "application/octet-stream"

        try:
            extra_args = {"ContentType": content_type}
            self.client.upload_file(
                Filename=str(path),
                Bucket=self.bucket_name,
                Key=object_key,
                ExtraArgs=extra_args,
            )
            logger.info("Uploaded artifact to R2", key=object_key, bucket=self.bucket_name)
            return True
        except ClientError as e:
            logger.error("Failed to upload file to R2", key=object_key, error=str(e))
            return False

    def upload_bytes(
        self,
        data: bytes,
        object_key: str,
        content_type: str = "application/octet-stream",
    ) -> bool:
        """Upload in-memory bytes to R2 bucket."""
        if not self.is_configured():
            return False

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=data,
                ContentType=content_type,
            )
            logger.info("Uploaded bytes to R2", key=object_key, bytes=len(data))
            return True
        except ClientError as e:
            logger.error("Failed to upload bytes to R2", key=object_key, error=str(e))
            return False

    def download_file(self, object_key: str, destination_path: Path | str) -> bool:
        """Download an object from R2 to a local destination."""
        if not self.is_configured():
            return False

        dest = Path(destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.client.download_file(
                Bucket=self.bucket_name,
                Key=object_key,
                Filename=str(dest),
            )
            logger.info("Downloaded artifact from R2", key=object_key, destination=str(dest))
            return True
        except ClientError as e:
            logger.error("Failed to download from R2", key=object_key, error=str(e))
            return False

    def get_object_bytes(self, object_key: str) -> Optional[bytes]:
        """Fetch bytes of an object directly from R2."""
        if not self.is_configured():
            return None

        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
            return response["Body"].read()
        except ClientError as e:
            logger.error("Failed to fetch object bytes from R2", key=object_key, error=str(e))
            return None

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
        except ClientError as e:
            logger.error("Failed to generate presigned URL for R2", key=object_key, error=str(e))
            return None

    def object_exists(self, object_key: str) -> bool:
        """Check whether an object key exists in R2."""
        if not self.is_configured():
            return False

        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False

    def list_objects(self, prefix: str = "") -> List[Dict[str, Any]]:
        """List object keys under a given prefix in R2."""
        if not self.is_configured():
            return []

        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
            )
            contents = response.get("Contents", [])
            return [
                {
                    "key": item["Key"],
                    "size": item["Size"],
                    "last_modified": item["LastModified"].isoformat(),
                }
                for item in contents
            ]
        except ClientError as e:
            logger.error("Failed to list R2 objects", prefix=prefix, error=str(e))
            return []


# Global singleton instance
storage_service = StorageService()

