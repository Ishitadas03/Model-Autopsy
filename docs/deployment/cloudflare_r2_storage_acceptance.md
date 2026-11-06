# Cloudflare R2 Artifact & Dataset Storage Integration Acceptance Report

**Date:** November 6, 2026  
**Status:** Verification Passed (12/12 Storage Tests, 116/116 ML Engine Tests)  
**Target Bucket:** `project9` (user provisioned)  
**Architecture:** Frontend on Vercel (`https://model-autopsy-ai.vercel.app`), Backend on Render (`https://model-autopsy-backend.onrender.com`), Database on Supabase PostgreSQL, Object Storage on Cloudflare R2 with observable local fallback.

---

## 1. Executive Summary

Production-grade Cloudflare R2 artifact and dataset storage has been implemented and validated across all eight phases. The implementation leverages the S3-compatible Cloudflare R2 API via `boto3` and `botocore` with strict connection timeouts (`connect_timeout=5`, `read_timeout=15`, `max_attempts=3`), SHA-256 integrity verification, atomic temp-file downloads, and an observable local filesystem fallback.

All 12 automated storage test scenarios pass in 0.72 seconds, and all 116 ML Engine tests pass in 51.92 seconds with zero regressions to scientific invariants.

---

## 2. Storage Partitioning Architecture

| Resource Category | Storage Location | Key Pattern / Path | Metadata Location |
| :--- | :--- | :--- | :--- |
| **Uploaded CSV Datasets** | Cloudflare R2 | `datasets/{dataset_id}/data.csv` | Supabase `datasets` table (`metadata_`: `sha256`, `storage_provider`, `storage_key`, `file_size_bytes`) |
| **Experiment Results** | Cloudflare R2 | `experiments/{experiment_id}/results.json` | Supabase `artifact_manifests` & `artifact_references` |
| **Degradation Curves** | Cloudflare R2 | `experiments/{experiment_id}/curves.csv` | Supabase `artifact_manifests` & `artifact_references` |
| **Audit Reports** | Cloudflare R2 | `experiments/{experiment_id}/report.md` | Supabase `artifact_manifests` & `artifact_references` |
| **Run Manifests** | Cloudflare R2 | `experiments/{experiment_id}/manifest.json` | Supabase `artifact_manifests` & `artifact_references` |
| **Structured Metrics & Failures** | Supabase PostgreSQL | `experiment_results`, `failed_samples` | Relational columns and JSONB payloads |

---

## 3. Storage Adapter Specifications (`backend/app/services/storage_service.py`)

### Core Capabilities
- **Direct S3 / R2 API Operations:**
  - `upload_file_to_r2(local_path, object_key, content_type)`
  - `upload_bytes_to_r2(data, object_key, content_type)`
  - `download_file_from_r2(object_key, destination_path)` — Atomic download writes to `.tmp_<pid>` and replaces target on completion.
  - `get_object_bytes_from_r2(object_key)`
  - `delete_object_from_r2(object_key)`
  - `generate_presigned_url(object_key, expiration_seconds)`
  - `object_exists_in_r2(object_key)`
  - `get_object_metadata_from_r2(object_key)`
  - `check_bucket_access()` — Non-destructive `head_bucket` inspection.
- **Unified Adapter with Resilient Local Fallback:**
  - `store_file(...)` -> `UploadResult`
  - `store_bytes(...)` -> `UploadResult`
  - `retrieve_file(...)` -> `bool`
  - `retrieve_bytes(...)` -> `Optional[bytes]`
  - `delete_object(...)` -> `bool`
  - `get_object_metadata(...)` -> `Optional[Dict[str, Any]]`
  - `active_provider`: returns `"r2"` when configured and accessible, otherwise `"local"`.
- **Integrity Verification:**
  - Automatic computation of SHA-256 hashes (`compute_sha256_bytes`, `compute_sha256_file`).
  - SHA-256 metadata attached to S3 objects and returned in `UploadResult`.
- **Fault Tolerance:**
  - Catching `(ClientError, BotoCoreError, Exception)` gracefully.
  - Fallback to local disk if R2 credentials are unset or network requests fail.

---

## 4. API Endpoints

### 4.1 Dataset Ingestion: `POST /api/v1/datasets/upload`
- **File Validation:**
  - Enforces `.csv` extension and `MAX_FILE_SIZE_BYTES` (25 MB).
  - Validates CSV structure: requires valid UTF-8/ISO-8859-1 decoding, $\ge 2$ columns, $\ge 1$ data row, consistent row length.
  - Automatically detects column types (`numeric` vs `categorical`), computes missing value counts, and extracts classification target classes.
- **Path Traversal Prevention:**
  - Strict regex `^[a-zA-Z0-9_\-]+$` for `dataset_id`.
  - Rejects directory traversal sequences (`..`, `/`, `\`).
- **Conflict Prevention:**
  - Rejects duplicate `dataset_id` with HTTP 409 Conflict.
- **Atomicity:**
  - Uploads raw CSV to `datasets/{dataset_id}/data.csv` first. If database registration fails, deletes the uploaded object to prevent orphaned storage.

### 4.2 Dataset Retrieval: `GET /api/v1/datasets/{dataset_id}/download`
- Retrieves storage key from Supabase `datasets.metadata_`.
- If R2 is active, returns HTTP 307 Redirect to a short-lived presigned download URL.
- Otherwise streams file directly with `Content-Disposition: attachment; filename="{filename}"` and `X-Storage-Provider` / `X-SHA256` headers.

### 4.3 Experiment Artifact Access: `GET /api/v1/experiments/{experiment_id}/artifacts/{artifact_type}`
- Checks local filesystem first for exact match or canonical aliases (`results.json`, `aggregate_comparison.json`, `curves.csv`, `report.md`, `manifest.json`).
- If missing locally, checks Cloudflare R2.
- Returns HTTP 307 Redirect to presigned URL, or streams bytes with appropriate MIME type.
- In `ArtifactService`, if a Render container restarts and local artifact files are cleared from ephemeral storage, missing artifacts are transparently re-downloaded from R2.

### 4.4 Health & Observability: `GET /api/v1/storage/status` & `GET /api/health`
- `GET /api/v1/storage/status`:
  ```json
  {
    "active_provider": "r2",
    "is_r2_configured": true,
    "bucket_name": "model-autopsy-artifacts",
    "bucket_accessible": true,
    "access_details": {
      "configured": true,
      "accessible": true,
      "bucket_name": "model-autopsy-artifacts",
      "active_provider": "r2",
      "error": null
    },
    "local_datasets_dir": "...",
    "local_artifacts_dir": "..."
  }
  ```
- `GET /api/health`: Exposes non-blocking storage summary without failing overall health check if R2 is temporarily unreachable.

---

## 5. Automated Verification Results

### Storage Test Suite (`backend/tests/test_storage_r2.py`)
```
backend/tests/test_storage_r2.py::test_1_upload_object_to_r2 PASSED      [  8%]
backend/tests/test_storage_r2.py::test_2_download_object_from_r2 PASSED  [ 16%]
backend/tests/test_storage_r2.py::test_3_object_existence_check PASSED   [ 25%]
backend/tests/test_storage_r2.py::test_4_delete_object_from_r2 PASSED    [ 33%]
backend/tests/test_storage_r2.py::test_5_fallback_when_credentials_missing_or_invalid PASSED [ 41%]
backend/tests/test_storage_r2.py::test_6_error_handling_when_bucket_does_not_exist PASSED [ 50%]
backend/tests/test_storage_r2.py::test_7_network_timeout_and_retry PASSED [ 58%]
backend/tests/test_storage_r2.py::test_8_safe_key_generation_and_path_traversal PASSED [ 66%]
backend/tests/test_storage_r2.py::test_9_dataset_validation PASSED       [ 75%]
backend/tests/test_storage_r2.py::test_10_artifact_retrieval_and_presigned_url PASSED [ 83%]
backend/tests/test_storage_r2.py::test_11_metadata_consistency PASSED    [ 91%]
backend/tests/test_storage_r2.py::test_12_failure_recovery_on_failed_storage PASSED [100%]

============================= 12 passed in 0.72s ==============================
```

### ML Engine Test Suite (`ml_engine/tests`)
```
====================== 116 passed, 8 warnings in 51.92s =======================
```

---

## 6. Production Deployment Configuration (Render)

To activate live Cloudflare R2 storage in production on Render, configure the following environment variables in the Render Dashboard (`model-autopsy-backend` service):

| Variable | Production Value | Sensitive |
| :--- | :--- | :--- |
| `R2_ACCOUNT_ID` | `916b7f70128acc095b09c70a1c1d6318` | No |
| `R2_ACCESS_KEY_ID` | `[CONFIGURED_IN_RENDER_DASHBOARD]` | Yes |
| `R2_SECRET_ACCESS_KEY` | `[CONFIGURED_IN_RENDER_DASHBOARD]` | Yes |
| `R2_BUCKET_NAME` | `project9` | No |
| `R2_ENDPOINT` / `R2_ENDPOINT_URL` | `https://916b7f70128acc095b09c70a1c1d6318.r2.cloudflarestorage.com` | No |
| `STORAGE_PROVIDER` | `auto` | No |

*Note: If credentials are not present, the backend automatically operates with the local persistent fallback.*

