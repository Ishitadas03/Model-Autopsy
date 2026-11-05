"""Model adapter endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.model_adapter import ModelAdapterRepository
from app.schemas import ModelAdapterSchema

router = APIRouter()


@router.get("", response_model=List[ModelAdapterSchema])
async def list_models(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    session: AsyncSession = Depends(get_session),
) -> List[ModelAdapterSchema]:
    """List supported pre-configured model adapters."""
    repo = ModelAdapterRepository(session)

    # Seed default adapters if empty
    await repo.seed_default_adapters()

    if dataset_id:
        models = await repo.get_by_dataset(dataset_id)
    else:
        models = await repo.get_active()

    return [_model_to_schema(m) for m in models]


@router.get("/{model_id}", response_model=ModelAdapterSchema)
async def get_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
) -> ModelAdapterSchema:
    """Get a specific model adapter by ID."""
    repo = ModelAdapterRepository(session)
    model = await repo.get_by_model_id(model_id)

    if not model:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found",
        )

    return _model_to_schema(model)


def _model_to_schema(model) -> ModelAdapterSchema:
    """Convert ModelAdapter model to ModelAdapterSchema."""
    return ModelAdapterSchema(
        id=model.model_id,
        name=model.name,
        description=model.description,
        taskType=model.task_type,
        supportedDatasets=[model.dataset_id],
        framework=model.framework,
        baselineF1=model.baseline_f1,
    )