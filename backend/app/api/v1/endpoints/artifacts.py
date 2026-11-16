"""Artifact endpoints for canonical experiment artifacts."""

from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.core.database import get_session
    from app.core.auth import get_current_user, assert_experiment_access
    from app.repositories.experiment import ExperimentRepository
except ImportError:
    from backend.app.core.database import get_session
    from backend.app.core.auth import get_current_user, assert_experiment_access
    from backend.app.repositories.experiment import ExperimentRepository

router = APIRouter()

ALLOWED_EXTENSIONS = {".json", ".csv", ".png", ".md", ".txt"}
MIME_MAP = {
    ".json": "application/json",
    ".csv": "text/csv; charset=utf-8",
    ".png": "image/png",
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}


class ArtifactFormat(str, Enum):
    """Artifact format enumeration."""
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


@router.get("/e003")
@router.get("/E003")
async def get_e003_artifact(
    format: str = Query("json", description="Output format: json, csv, or markdown"),
    user_id: Optional[UUID] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get E003 canonical experiment artifact in specified format."""
    try:
        from app.services.artifact_service import ArtifactService
    except ImportError:
        from backend.app.services.artifact_service import ArtifactService

    service = ArtifactService(session)
    return await service.get_e003_artifact(format)


@router.get("/{experiment_id}/artifacts/{artifact_type}")
async def get_experiment_artifact(
    experiment_id: str,
    artifact_type: str,
    seed: Optional[int] = Query(None, description="Specific seed (null for aggregated)"),
    format: str = Query("json", description="Output format: json, csv, or markdown"),
    user_id: Optional[UUID] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get experiment artifact by filename or artifact type."""
    try:
        from app.services.artifact_service import ArtifactService
        from app.core.exceptions import ArtifactNotFoundError
    except ImportError:
        from backend.app.services.artifact_service import ArtifactService
        from backend.app.core.exceptions import ArtifactNotFoundError

    # Authenticate and authorize BEFORE reading local paths or generating signed R2 URLs.
    exp_repo = ExperimentRepository(session)
    experiment = await exp_repo.get_by_experiment_id(experiment_id)
    if not experiment:
        try:
            experiment = await exp_repo.get_with_details(UUID(experiment_id))
        except ValueError:
            pass
    assert_experiment_access(experiment, user_id)

    service = ArtifactService(session)
    try:
        return await service.get_artifact(experiment.id, artifact_type, seed, format)
    except ArtifactNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
