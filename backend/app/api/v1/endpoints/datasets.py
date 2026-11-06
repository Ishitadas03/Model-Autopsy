"""Dataset endpoints for listing, inspection, CSV upload, and artifact download."""

import csv
import io
import re
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.core.database import get_session
    from app.repositories.dataset import DatasetRepository
    from app.schemas import DatasetSchema
    from app.services.storage_service import storage_service
except ImportError:
    from backend.app.core.database import get_session
    from backend.app.repositories.dataset import DatasetRepository
    from backend.app.schemas import DatasetSchema
    from backend.app.services.storage_service import storage_service

router = APIRouter()

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_and_parse_csv(
    content: bytes,
    target_name: Optional[str] = None,
) -> dict:
    """Validate CSV structure, check columns/rows, infer feature types and target classes."""
    text = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to decode CSV file. Please upload a valid UTF-8 encoded CSV file.",
        )

    f = io.StringIO(text)
    sample_text = text[:4096]
    delimiter = ","
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=",\t;")
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ","

    f.seek(0)
    reader = csv.reader(f, delimiter=delimiter)
    try:
        header = next(reader, None)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV header: {str(e)}",
        )

    if not header or len(header) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must contain at least 2 columns (features and target).",
        )

    clean_header = [col.strip() for col in header]
    if len(clean_header) != len(set(clean_header)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV header contains duplicate column names.",
        )

    rows = []
    for row_idx, row in enumerate(reader):
        if not row or all(c.strip() == "" for c in row):
            continue
        if len(row) != len(clean_header):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Row {row_idx + 1} column count ({len(row)}) does not match header count ({len(clean_header)}).",
            )
        rows.append(row)

    if len(rows) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must contain at least 1 row of data.",
        )

    # Determine target column
    if target_name:
        if target_name not in clean_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target column '{target_name}' not found in CSV columns: {clean_header}",
            )
        target_col = target_name
    else:
        target_col = clean_header[-1]

    feature_cols = [c for c in clean_header if c != target_col]
    target_idx = clean_header.index(target_col)

    # Infer column data types and missing counts
    structured_features = []
    for col_name in feature_cols:
        col_idx = clean_header.index(col_name)
        missing_count = 0
        is_numeric = True
        for r in rows:
            val = r[col_idx].strip()
            if val in ("", "NA", "NaN", "null", "None"):
                missing_count += 1
            else:
                try:
                    float(val)
                except ValueError:
                    is_numeric = False

        structured_features.append({
            "name": col_name,
            "type": "numeric" if is_numeric else "categorical",
            "missingCount": missing_count,
        })

    # Target classes inspection
    target_values = set()
    for r in rows:
        val = r[target_idx].strip()
        if val != "":
            target_values.add(val)
    class_names = sorted(list(target_values)) if len(target_values) <= 50 else None

    return {
        "sample_count": len(rows),
        "feature_count": len(feature_cols),
        "target_col": target_col,
        "feature_names": structured_features,
        "class_names": class_names,
    }


@router.get("", response_model=List[DatasetSchema])
async def list_datasets(
    session: AsyncSession = Depends(get_session),
) -> List[DatasetSchema]:
    """List available benchmark datasets registered in the system."""
    repo = DatasetRepository(session)

    # Seed default datasets if empty
    await repo.seed_default_datasets()

    datasets = await repo.get_active()
    return [_dataset_to_schema(ds) for ds in datasets]


@router.post("/upload", response_model=DatasetSchema, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV dataset file"),
    dataset_id: Optional[str] = Form(None, description="Unique alphanumeric identifier (e.g., 'customer-churn')"),
    name: Optional[str] = Form(None, description="Human-readable name of the dataset"),
    description: Optional[str] = Form("", description="Description of dataset contents"),
    task_type: str = Form("classification", description="Task type: 'classification' or 'regression'"),
    target_name: Optional[str] = Form(None, description="Name of the target/label column (defaults to last column)"),
    session: AsyncSession = Depends(get_session),
) -> DatasetSchema:
    """Upload a new CSV dataset, validate schema, store in R2/local storage, and persist in Supabase."""
    # 1. Validate file extension and size
    filename = file.filename or "dataset.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files (.csv) are accepted for dataset upload.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 2. Validate dataset ID and check path traversal
    if dataset_id:
        cleaned_id = dataset_id.strip()
        if not SAFE_ID_REGEX.match(cleaned_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="dataset_id may only contain alphanumeric characters, hyphens, and underscores.",
            )
    else:
        # Generate safe slug from name or uuid
        if name:
            slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", name.strip().lower()).strip("-")
            cleaned_id = slug if slug else f"dataset-{uuid.uuid4().hex[:8]}"
        else:
            cleaned_id = f"dataset-{uuid.uuid4().hex[:8]}"

    # Check for duplicate ID in Supabase
    repo = DatasetRepository(session)
    existing = await repo.get_by_dataset_id(cleaned_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A dataset with ID '{cleaned_id}' already exists.",
        )

    # 3. Parse and validate CSV data
    parsed_info = validate_and_parse_csv(content, target_name=target_name)

    # 4. Store in Cloudflare R2 / Local fallback
    object_key = f"datasets/{cleaned_id}/data.csv"
    try:
        upload_res = storage_service.store_bytes(
            data=content,
            object_key=object_key,
            content_type="text/csv; charset=utf-8",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store dataset in object storage: {str(e)}",
        )

    # 5. Persist Dataset record in Supabase
    dataset_name = name.strip() if name and name.strip() else cleaned_id.replace("-", " ").title()
    metadata_ = {
        "storage_provider": upload_res.provider,
        "storage_key": upload_res.key,
        "sha256": upload_res.sha256_hash,
        "file_size_bytes": upload_res.size_bytes,
        "original_filename": filename,
        "url": upload_res.url,
    }

    try:
        new_dataset = await repo.create(
            dataset_id=cleaned_id,
            name=dataset_name,
            description=description.strip() if description else "",
            task_type=task_type,
            sample_count=parsed_info["sample_count"],
            feature_count=parsed_info["feature_count"],
            license="Custom / User Uploaded",
            tags=["custom", "user-upload", task_type],
            feature_names=parsed_info["feature_names"],
            target_name=parsed_info["target_col"],
            class_names=parsed_info["class_names"],
            metadata_=metadata_,
        )
    except Exception as e:
        # Rollback storage object on database insertion failure to ensure consistency
        storage_service.delete_object(object_key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register dataset in database: {str(e)}",
        )

    return _dataset_to_schema(new_dataset)


@router.get("/{dataset_id}/download")
async def download_dataset(
    dataset_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Download the raw CSV dataset file from Cloudflare R2 or local fallback storage."""
    repo = DatasetRepository(session)
    dataset = await repo.get_by_dataset_id(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{dataset_id}' not found.",
        )

    storage_key = (dataset.metadata_ or {}).get("storage_key") or f"datasets/{dataset_id}/data.csv"

    # If R2 is active and object exists, generate presigned URL
    if storage_service.is_configured() and storage_service.object_exists_in_r2(storage_key):
        presigned_url = storage_service.generate_presigned_url(storage_key)
        if presigned_url:
            return RedirectResponse(url=presigned_url, status_code=307)

    # Otherwise stream or return bytes
    content = storage_service.retrieve_bytes(storage_key)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Storage object for dataset '{dataset_id}' not found.",
        )

    filename = (dataset.metadata_ or {}).get("original_filename") or f"{dataset_id}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Storage-Provider": (dataset.metadata_ or {}).get("storage_provider", "local"),
            "X-SHA256": (dataset.metadata_ or {}).get("sha256", ""),
        },
    )


@router.get("/{dataset_id}", response_model=DatasetSchema)
async def get_dataset(
    dataset_id: str,
    session: AsyncSession = Depends(get_session),
) -> DatasetSchema:
    """Get a specific dataset by ID."""
    repo = DatasetRepository(session)
    dataset = await repo.get_by_dataset_id(dataset_id)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found",
        )

    return _dataset_to_schema(dataset)


def _dataset_to_schema(dataset) -> DatasetSchema:
    """Convert Dataset model to DatasetSchema with structured features list."""
    features = []
    if dataset.feature_names:
        for f in dataset.feature_names:
            if isinstance(f, dict):
                features.append(f)
            else:
                features.append({
                    "name": str(f),
                    "type": "numeric",
                    "missingCount": 0,
                })

    class_cnt = len(dataset.class_names) if dataset.class_names else None
    is_custom = bool(dataset.metadata_ and dataset.metadata_.get("storage_provider"))

    return DatasetSchema(
        id=dataset.dataset_id,
        name=dataset.name,
        description=dataset.description or "",
        taskType=dataset.task_type,
        sampleCount=dataset.sample_count,
        featureCount=dataset.feature_count,
        classCount=class_cnt,
        license=dataset.license or "CC-BY-4.0",
        tags=dataset.tags or [],
        isCustom=is_custom,
        features=features,
    )
