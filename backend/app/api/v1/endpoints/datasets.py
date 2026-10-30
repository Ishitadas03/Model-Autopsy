"""Dataset endpoints."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.repositories.dataset import DatasetRepository
from backend.app.schemas import DatasetSchema

router = APIRouter()


@router.get("", response_model=List[DatasetSchema])
async def list_datasets(
    session: AsyncSession = Depends(get_session),
) -> List[DatasetSchema]:
    """List available benchmark datasets registered in the system."""
    print("DEBUG DATASETS SESSION BIND:", getattr(session, "bind", None))
    repo = DatasetRepository(session)

    # Seed default datasets if empty
    await repo.seed_default_datasets()

    datasets = await repo.get_active()
    return [_dataset_to_schema(ds) for ds in datasets]


@router.get("/{dataset_id}", response_model=DatasetSchema)
async def get_dataset(
    dataset_id: str,
    session: AsyncSession = Depends(get_session),
) -> DatasetSchema:
    """Get a specific dataset by ID."""
    repo = DatasetRepository(session)
    dataset = await repo.get_by_dataset_id(dataset_id)

    if not dataset:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found",
        )

    return _dataset_to_schema(dataset)


def _dataset_to_schema(dataset) -> DatasetSchema:
    """Convert Dataset model to DatasetSchema."""
    return DatasetSchema(
        id=dataset.dataset_id,
        name=dataset.name,
        description=dataset.description,
        taskType=dataset.task_type,
        sampleCount=dataset.sample_count,
        featureCount=dataset.feature_count,
        license=dataset.license,
        tags=dataset.tags or [],
    )