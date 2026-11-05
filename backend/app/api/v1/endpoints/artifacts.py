"""Artifact endpoints for canonical experiment artifacts."""

from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.repositories.artifact import ArtifactRepository
from app.repositories.experiment import ExperimentRepository

router = APIRouter()


class ArtifactFormat(str, Enum):
    """Artifact format enumeration."""

    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


@router.get("/e003")
async def get_e003_artifact(
    format: str = Query("json", description="Output format: json, csv, or markdown"),
    session: AsyncSession = Depends(get_session),
):
    """Get E003 canonical experiment artifact in specified format."""
    from app.services.artifact_service import ArtifactService

    service = ArtifactService(session)
    return await service.get_e003_artifact(format)


@router.get("/{experiment_id}/artifacts/{artifact_type}")
async def get_experiment_artifact(
    experiment_id: str,
    artifact_type: str,
    seed: Optional[int] = Query(None, description="Specific seed (null for aggregated)"),
    format: str = Query("json", description="Output format: json, csv, or markdown"),
    session: AsyncSession = Depends(get_session),
):
    """Get experiment artifact by type."""
    from app.services.artifact_service import ArtifactService
    from app.core.exceptions import ArtifactNotFoundError

    exp_repo = ExperimentRepository(session)

    # Find experiment
    experiment = await exp_repo.get_by_experiment_id(experiment_id)
    if not experiment:
        try:
            uuid_id = UUID(experiment_id)
            experiment = await exp_repo.get_with_details(uuid_id)
        except ValueError:
            pass

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    service = ArtifactService(session)
    try:
        return await service.get_artifact(experiment.id, artifact_type, seed, format)
    except ArtifactNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )