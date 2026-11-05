"""Artifact endpoints for canonical experiment artifacts."""

from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.core.config import settings
    from app.core.database import get_session
    from app.repositories.experiment import ExperimentRepository
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.database import get_session
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
    session: AsyncSession = Depends(get_session),
):
    """Get experiment artifact by filename or artifact type."""
    try:
        from app.services.artifact_service import ArtifactService
        from app.core.exceptions import ArtifactNotFoundError
    except ImportError:
        from backend.app.services.artifact_service import ArtifactService
        from backend.app.core.exceptions import ArtifactNotFoundError

    base_dir = settings.ARTIFACTS_BASE_DIR.resolve()
    exp_dir = (base_dir / experiment_id).resolve()
    target_path = (exp_dir / artifact_type).resolve()

    # 1. Path traversal security check
    if not target_path.is_relative_to(exp_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid path traversal sequence.",
        )

    # 2. Check canonical aliases if exact target does not exist
    if not (target_path.exists() and target_path.is_file()):
        aliases = {
            "results.json": [
                "aggregate_comparison.json",
                "aggregate_results.json",
                "results.json",
                "failure_patterns_summary.json",
                "metrics.json",
            ],
            "curves.csv": [
                "aggregate_comparison.csv",
                "aggregate_results.csv",
                "results.csv",
                "curves.csv",
                "sample_level_metrics.csv",
                "feature_vulnerability_summary.csv",
                "shift_summary.csv",
            ],
            "report.md": ["report.md"],
            "manifest.json": ["manifest.json", "reproducibility_manifest.json"],
        }
        for cand in aliases.get(artifact_type.lower(), []):
            cand_p = (exp_dir / cand).resolve()
            if cand_p.exists() and cand_p.is_file():
                target_path = cand_p
                break

    # 3. If literal or aliased file exists in artifact directory, serve it directly
    if target_path.exists() and target_path.is_file():
        suffix = target_path.suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="File extension not permitted.",
            )
        return FileResponse(
            path=target_path,
            filename=target_path.name,
            media_type=MIME_MAP.get(suffix, "application/octet-stream"),
        )

    # 2b. If local file is missing, check Cloudflare R2 object storage
    try:
        try:
            from app.services.storage_service import storage_service
        except ImportError:
            from backend.app.services.storage_service import storage_service
        if storage_service.is_configured():
            r2_key = f"experiments/{experiment_id}/{artifact_type}"
            if storage_service.object_exists(r2_key):
                presigned = storage_service.generate_presigned_url(r2_key)
                if presigned:
                    from fastapi.responses import RedirectResponse
                    return RedirectResponse(url=presigned, status_code=307)
    except Exception:
        pass

    # 3. Otherwise try database lookup for dynamic experiment runs
    exp_repo = ExperimentRepository(session)
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
            detail=f"Experiment '{experiment_id}' or artifact '{artifact_type}' not found",
        )

    service = ArtifactService(session)
    try:
        return await service.get_artifact(experiment.id, artifact_type, seed, format)
    except ArtifactNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
