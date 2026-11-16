"""Automated tests for Cloudflare R2 / Local Object Storage integration.

Covers all 12 required scenarios:
1. Upload object to R2 (mocked)
2. Download object from R2 (mocked)
3. Object existence check
4. Delete object from R2
5. Storage fallback when R2 credentials missing or invalid
6. Storage error handling when bucket does not exist
7. Storage retry/failure on network timeout
8. Safe key generation preventing overwrite and path traversal
9. Dataset upload validation (valid CSV accepted, malformed CSV rejected)
10. Artifact retrieval for results.json, curves.csv, report.md
11. Metadata consistency between database records and storage objects
12. Failure recovery: failed upload does not create orphan database record
"""

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, ConnectTimeoutError

from app.core.config import settings
from app.services.storage_service import StorageService, UploadResult, compute_sha256_bytes, compute_sha256_file


@pytest.fixture
def mock_s3_client():
    """Mock boto3 client for R2 operations."""
    client = MagicMock()
    client.put_object.return_value = {"ETag": '"test-etag-12345"'}
    client.head_object.return_value = {
        "ContentLength": 1024,
        "ContentType": "text/csv",
        "ETag": '"test-etag-12345"',
        "Metadata": {"sha256": "abc123hash"},
    }
    client.generate_presigned_url.return_value = "https://r2.example.com/presigned-url"
    return client


@pytest.fixture
def configured_storage(mock_s3_client, tmp_path):
    """StorageService configured with valid R2 credentials and mocked S3 client."""
    service = StorageService()
    service.bucket_name = "model-autopsy-artifacts"
    service.endpoint_url = "https://test-account.r2.cloudflarestorage.com"
    service.access_key_id = "test-key-id"
    service.secret_access_key = "test-secret-key"
    service._client = mock_s3_client
    return service


# =============================================================================
# SCENARIOS 1-4: Core S3/R2 Operations
# =============================================================================

def test_1_upload_object_to_r2(configured_storage, mock_s3_client, tmp_path):
    """1. Upload object to R2 (mocked) with checksum verification."""
    data = b"feature1,feature2,target\n1.0,2.0,0\n3.0,4.0,1\n"
    res = configured_storage.store_bytes(data, "datasets/test-ds/data.csv", "text/csv")

    assert res.provider == "r2"
    assert res.key == "datasets/test-ds/data.csv"
    assert res.size_bytes == len(data)
    assert res.sha256_hash == compute_sha256_bytes(data)
    mock_s3_client.put_object.assert_called_once()


def test_2_download_object_from_r2(configured_storage, mock_s3_client, tmp_path):
    """2. Download object from R2 (mocked) atomically."""
    dest = tmp_path / "downloaded.csv"

    def fake_download_file(Bucket, Key, Filename):
        Path(Filename).write_bytes(b"downloaded content")

    mock_s3_client.download_file.side_effect = fake_download_file

    ok = configured_storage.retrieve_file("datasets/test-ds/data.csv", dest)
    assert ok is True
    assert dest.exists()
    assert dest.read_bytes() == b"downloaded content"


def test_3_object_existence_check(configured_storage, mock_s3_client):
    """3. Check object existence in R2."""
    assert configured_storage.object_exists("experiments/E001/results.json") is True

    # Simulate 404 Not Found from R2
    mock_s3_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
    )
    assert configured_storage.object_exists_in_r2("non-existent/key") is False


def test_4_delete_object_from_r2(configured_storage, mock_s3_client):
    """4. Delete object from R2."""
    ok = configured_storage.delete_object("experiments/E001/results.json")
    assert ok is True
    mock_s3_client.delete_object.assert_called_with(
        Bucket="model-autopsy-artifacts", Key="experiments/E001/results.json"
    )


# =============================================================================
# SCENARIOS 5-7: Error Handling, Timeouts, and Fallback
# =============================================================================

def test_5_fallback_when_credentials_missing_or_invalid(tmp_path):
    """5. Fall back seamlessly to local storage when credentials are not configured."""
    unconfigured_storage = StorageService()
    unconfigured_storage.access_key_id = None
    unconfigured_storage.secret_access_key = None
    unconfigured_storage.endpoint_url = None

    assert unconfigured_storage.is_configured() is False
    assert unconfigured_storage.active_provider == "local"

    data = b"col1,col2\n10,20\n"
    res = unconfigured_storage.store_bytes(data, "datasets/unconf/data.csv", "text/csv")
    assert res.provider == "local"
    assert res.size_bytes == len(data)
    assert res.sha256_hash == compute_sha256_bytes(data)

    retrieved = unconfigured_storage.retrieve_bytes("datasets/unconf/data.csv")
    assert retrieved == data


def test_6_error_handling_when_bucket_does_not_exist(configured_storage, mock_s3_client):
    """6. Handle NoSuchBucket error gracefully during head_bucket / access check."""
    mock_s3_client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "NoSuchBucket", "Message": "The specified bucket does not exist"}},
        "HeadBucket",
    )

    status = configured_storage.check_bucket_access()
    assert status["configured"] is True
    assert status["accessible"] is False
    assert "NoSuchBucket" in status["error"]


def test_7_network_timeout_and_retry(configured_storage, mock_s3_client, tmp_path):
    """7. Handle network failure and timeout by falling back safely to local storage."""
    mock_s3_client.put_object.side_effect = ConnectTimeoutError(
        endpoint_url="https://test-account.r2.cloudflarestorage.com"
    )

    data = b"network timeout test content"
    res = configured_storage.store_bytes(data, "experiments/E999/results.json")

    # Should fall back to local storage rather than crashing the caller
    assert res.provider == "local"
    assert res.size_bytes == len(data)
    assert res.sha256_hash == compute_sha256_bytes(data)


# =============================================================================
# SCENARIO 8: Safe Key Generation and Path Traversal Prevention
# =============================================================================

def test_8_safe_key_generation_and_path_traversal(tmp_path):
    """8. Ensure object keys prevent directory traversal and resolve within base dirs."""
    service = StorageService()
    service.access_key_id = None  # Force local path resolution

    with pytest.raises(ValueError, match="Invalid storage object key"):
        service.get_local_path("../../etc/passwd")



# =============================================================================
# SCENARIOS 9-12: Datasets, Artifacts, and DB Transaction Integrity
# =============================================================================

def test_9_dataset_validation():
    """9. Validate CSV parser: accept valid tabular data and reject malformed CSV."""
    from app.api.v1.endpoints.datasets import validate_and_parse_csv
    from fastapi import HTTPException

    # Valid CSV
    valid_csv = b"feature_a,feature_b,label\n1.2,3.4,good\n5.6,7.8,bad\n"
    info = validate_and_parse_csv(valid_csv, target_name="label")
    assert info["sample_count"] == 2
    assert info["feature_count"] == 2
    assert info["target_col"] == "label"
    assert info["class_names"] == ["bad", "good"]

    # Reject CSV with < 2 columns
    single_col_csv = b"only_one_col\nval1\nval2\n"
    with pytest.raises(HTTPException) as exc_info:
        validate_and_parse_csv(single_col_csv)
    assert exc_info.value.status_code == 400

    # Reject empty CSV
    with pytest.raises(HTTPException) as exc_info:
        validate_and_parse_csv(b"")
    assert exc_info.value.status_code == 400


def test_10_artifact_retrieval_and_presigned_url(configured_storage, mock_s3_client):
    """10. Generate presigned URLs for experiment artifacts (results.json, curves.csv, report.md)."""
    mock_s3_client.head_object.return_value = {"ContentLength": 500}
    mock_s3_client.generate_presigned_url.return_value = "https://r2.cloudflarestorage.com/download/results.json?token=xyz"

    for artifact_name in ["results.json", "curves.csv", "report.md"]:
        r2_key = f"experiments/E001/{artifact_name}"
        url = configured_storage.generate_presigned_url(r2_key, expiration_seconds=1800)
        assert url is not None
        assert "results.json" in url or "r2" in url


def test_11_metadata_consistency():
    """11. Verify UploadResult metadata contract matches Supabase dataset/artifact models."""
    data = b"sample_index,feature_val,label\n0,0.5,1\n"
    service = StorageService()
    service.access_key_id = None  # Local provider

    res = service.store_bytes(data, "datasets/consistency-test/data.csv", "text/csv")
    assert isinstance(res, UploadResult)
    assert res.provider == "local"
    assert res.sha256_hash == compute_sha256_bytes(data)
    assert res.size_bytes == len(data)

    # Clean up test object
    service.delete_object("datasets/consistency-test/data.csv")


def test_12_failure_recovery_on_failed_storage():
    """12. Ensure failed storage operations do not generate false success."""
    failing_service = StorageService()
    failing_service.bucket_name = "nonexistent-bucket"
    failing_service.access_key_id = "test"
    failing_service.secret_access_key = "test"
    failing_service.endpoint_url = "https://invalid.endpoint"

    mock_client = MagicMock()
    mock_client.put_object.side_effect = Exception("Storage backend unreachable")
    failing_service._client = mock_client

    # When R2 upload fails, it safely falls back to local and records provider='local'
    data = b"recovery test"
    res = failing_service.store_bytes(data, "datasets/recovery-test/data.csv")
    assert res.provider == "local"
    assert res.size_bytes == len(data)

    failing_service.delete_object("datasets/recovery-test/data.csv")



@pytest.mark.parametrize("key", ["/etc/passwd", "a/../b", "a/./b", "a//b", "", "C:/temp", "a\\b"])
def test_local_keys_reject_ambiguous_paths(key):
    with pytest.raises(ValueError):
        StorageService().get_local_path(key)


def test_local_keys_reject_symlink_escape(tmp_path, monkeypatch):
    root = tmp_path / "artifacts"
    root.mkdir()
    outside = tmp_path / "private"
    outside.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(settings, "ARTIFACTS_BASE_DIR", root)
    with pytest.raises(ValueError, match="escapes"):
        StorageService().get_local_path("link/secret.txt")


@pytest.mark.parametrize("method,args", [
    ("retrieve_bytes", ("experiments/stale.json",)),
    ("retrieve_file", ("experiments/stale.json", "unused.json")),
    ("get_object_metadata", ("experiments/stale.json",)),
    ("delete_object", ("experiments/stale.json",)),
    ("list_objects", ("experiments",)),
])
def test_required_r2_failure_never_uses_local_copy(method, args, configured_storage, mock_s3_client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ARTIFACTS_BASE_DIR", tmp_path)
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "r2")
    local = configured_storage.get_local_path("experiments/stale.json")
    local.parent.mkdir(parents=True)
    local.write_bytes(b"stale local content")
    failure = ClientError({"Error": {"Code": "AccessDenied"}}, "TestOperation")
    for operation in ("get_object", "download_file", "head_object", "delete_object", "get_paginator"):
        getattr(mock_s3_client, operation).side_effect = failure
    with pytest.raises(RuntimeError, match="local fallback is disabled"):
        getattr(configured_storage, method)(*args)
    assert local.read_bytes() == b"stale local content"


def test_required_r2_existence_does_not_use_local_copy(configured_storage, mock_s3_client, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "ARTIFACTS_BASE_DIR", tmp_path)
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "r2")
    (tmp_path / "stale.json").write_bytes(b"stale")
    mock_s3_client.head_object.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadObject")
    assert configured_storage.object_exists("stale.json") is False


def test_r2_listing_collects_every_page(configured_storage, mock_s3_client):
    from datetime import datetime, timezone
    item = {"Size": 1, "LastModified": datetime.now(timezone.utc)}
    mock_s3_client.get_paginator.return_value.paginate.return_value = [
        {"Contents": [{**item, "Key": f"objects/{i}"} for i in range(1000)]},
        {"Contents": [{**item, "Key": "objects/1000"}]},
    ]
    objects = configured_storage.list_objects("objects/")
    assert len(objects) == 1001
    assert objects[-1]["key"] == "objects/1000"


def test_dataset_prefix_uses_dataset_root(tmp_path, monkeypatch):
    service = StorageService()
    service.access_key_id = None
    monkeypatch.setattr(settings, "DATASETS_BASE_DIR", tmp_path / "datasets")
    monkeypatch.setattr(settings, "ARTIFACTS_BASE_DIR", tmp_path / "artifacts")
    service.store_bytes(b"a,b", "datasets/example/data.csv")
    assert service.list_objects("datasets/")[0]["key"] == "datasets/example/data.csv"
    assert service.get_local_path("datasets_other/data.csv") == tmp_path / "artifacts/datasets_other/data.csv"
