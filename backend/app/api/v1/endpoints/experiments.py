"""Experiment endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_session
from backend.app.repositories.experiment import ExperimentRepository, ExperimentRunRepository, ExperimentResultRepository
from backend.app.schemas import (
    ExperimentSummarySchema,
    ExperimentDetailSchema,
    ExperimentRunRequest,
    ExperimentProgressSchema,
    ExperimentCancelResponse,
    RunStatus,
)

router = APIRouter()


@router.get("", response_model=List[ExperimentSummarySchema])
async def list_experiments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> List[ExperimentSummarySchema]:
    """List all submitted and completed autopsy experiments."""
    repo = ExperimentRepository(session)

    if status:
        try:
            run_status = RunStatus(status)
            experiments = await repo.get_by_status(run_status, skip, limit)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}",
            )
    else:
        experiments = await repo.get_all(skip, limit)

    return [_experiment_to_summary(exp) for exp in experiments]


@router.get("/{experiment_id}", response_model=ExperimentDetailSchema)
async def get_experiment(
    experiment_id: str,
    session: AsyncSession = Depends(get_session),
) -> ExperimentDetailSchema:
    """Fetch status, telemetry, and results for a single experiment."""
    repo = ExperimentRepository(session)

    # Try to find by experiment_id (e.g., EXP-0241) first
    experiment = await repo.get_by_experiment_id(experiment_id)

    # If not found, try by UUID
    if not experiment:
        try:
            uuid_id = UUID(experiment_id)
            experiment = await repo.get_with_details(uuid_id)
        except ValueError:
            pass

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    return _experiment_to_detail(experiment)


@router.post("", response_model=ExperimentDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    request: ExperimentRunRequest,
    session: AsyncSession = Depends(get_session),
) -> ExperimentDetailSchema:
    """Submit a new stress-testing autopsy job."""
    from backend.app.services.experiment_service import ExperimentService

    service = ExperimentService(session)
    experiment = await service.create_experiment(request)
    return _experiment_to_detail(experiment)


@router.post("/{experiment_id}/cancel", response_model=ExperimentCancelResponse)
async def cancel_experiment(
    experiment_id: str,
    session: AsyncSession = Depends(get_session),
) -> ExperimentCancelResponse:
    """Request cancellation of an actively running or queued experiment."""
    from backend.app.services.experiment_service import ExperimentService
    from backend.app.core.exceptions import ExperimentNotFoundError

    service = ExperimentService(session)

    # Try to find by experiment_id first
    repo = ExperimentRepository(session)
    experiment = await repo.get_by_experiment_id(experiment_id)
    if not experiment:
        try:
            uuid_id = UUID(experiment_id)
            experiment = await repo.get_with_details(uuid_id)
        except ValueError:
            pass

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    try:
        await service.cancel_experiment(experiment.id)
        return ExperimentCancelResponse(success=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{experiment_id}/progress", response_model=ExperimentProgressSchema)
async def get_experiment_progress(
    experiment_id: str,
    session: AsyncSession = Depends(get_session),
) -> ExperimentProgressSchema:
    """Get real-time progress for a running experiment."""
    repo = ExperimentRepository(session)

    experiment = await repo.get_by_experiment_id(experiment_id)
    if not experiment:
        try:
            uuid_id = UUID(experiment_id)
            experiment = await repo.get_with_details(uuid_id)
        except ValueError:
            pass

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment {experiment_id} not found",
        )

    return ExperimentProgressSchema(
        experiment_id=experiment.experiment_id,
        status=RunStatus(experiment.status.value),
        progress_percent=experiment.progress_percent,
        current_seed_index=experiment.current_seed_index,
        current_severity_index=experiment.current_severity_index,
        total_seeds=len(experiment.seeds) if experiment.seeds else 1,
        total_severities=len(experiment.severity_levels) if experiment.severity_levels else 1,
        error_message=experiment.error_message,
    )


def _experiment_to_summary(experiment) -> ExperimentSummarySchema:
    """Convert Experiment model to ExperimentSummarySchema."""
    result = experiment.result
    return ExperimentSummarySchema(
        id=experiment.experiment_id,
        modelName=experiment.model_name,
        datasetName=experiment.dataset_name,
        datasetId=experiment.dataset_id,
        taskType=experiment.task_type.value,
        perturbationFamily=experiment.perturbation_family.value,
        noiseType=experiment.noise_type,
        evaluationMetric=experiment.evaluation_metric,
        failureThreshold=experiment.failure_threshold,
        seed=experiment.seed,
        status=RunStatus(experiment.status.value),
        progressPercent=experiment.progress_percent,
        createdAt=experiment.created_at.isoformat() + "Z",
        results=_build_results(result) if result else None,
    )


def _experiment_to_detail(experiment) -> ExperimentDetailSchema:
    """Convert Experiment model to ExperimentDetailSchema."""
    summary = _experiment_to_summary(experiment)
    return ExperimentDetailSchema(
        **summary.model_dump(),
        runs=[
            {
                "seed": run.seed,
                "status": RunStatus(run.status.value),
                "progress_percent": run.progress_percent,
                "current_severity": run.current_severity,
                "error_message": run.error_message,
            }
            for run in experiment.runs
        ],
        config_yaml=experiment.config_yaml,
        severity_levels=experiment.severity_levels,
        seeds=experiment.seeds,
        stress_mode=experiment.stress_mode.value,
        started_at=experiment.started_at.isoformat() + "Z" if experiment.started_at else None,
        completed_at=experiment.completed_at.isoformat() + "Z" if experiment.completed_at else None,
    )


def _build_results(result) -> dict:
    """Build results dict from ExperimentResult model."""
    if not result:
        return None

    return {
        "baselineScore": result.baseline_macro_f1,
        "worstCaseScore": result.worst_case_macro_f1,
        "observedBoundary": result.observed_boundary,
        "failedSamplesCount": result.failed_samples_count,
        "curveData": result.curve_data or [],
        "featureVulnerabilities": result.feature_vulnerabilities or [],
    }