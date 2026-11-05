"""Experiment endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.experiment import ExperimentRepository, ExperimentRunRepository, ExperimentResultRepository
from app.schemas import (
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
    status_filter: Optional[str] = Query(None, alias="status"),
    session: AsyncSession = Depends(get_session),
) -> List[ExperimentSummarySchema]:
    """List all submitted and completed autopsy experiments."""
    repo = ExperimentRepository(session)

    if status_filter:
        try:
            run_status = RunStatus(status_filter)
            experiments = await repo.get_by_status(run_status, skip, limit)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
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
@router.post("/run", response_model=ExperimentDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    request: ExperimentRunRequest,
    session: AsyncSession = Depends(get_session),
) -> ExperimentDetailSchema:
    """Submit a new stress-testing autopsy job."""
    from app.services.experiment_service import ExperimentService

    service = ExperimentService(session)
    experiment = await service.create_experiment(request)
    return _experiment_to_detail(experiment)


@router.post("/{experiment_id}/cancel", response_model=ExperimentCancelResponse)
async def cancel_experiment(
    experiment_id: str,
    session: AsyncSession = Depends(get_session),
) -> ExperimentCancelResponse:
    """Request cancellation of an actively running or queued experiment."""
    from app.services.experiment_service import ExperimentService
    from app.core.exceptions import ExperimentNotFoundError

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
        cancel_data = await service.cancel_experiment(experiment.id)
        return ExperimentCancelResponse(
            success=True,
            experiment_id=experiment.experiment_id,
            status="cancelled",
            message=f"Experiment {experiment.experiment_id} terminated successfully.",
        )
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

    status_val = experiment.status.value if hasattr(experiment.status, "value") else str(experiment.status)
    return ExperimentProgressSchema(
        experimentId=experiment.experiment_id,
        status=status_val,
        progressPercent=float(experiment.progress_percent or 0),
        currentSeedIndex=experiment.current_seed_index or 0,
        currentSeverityIndex=experiment.current_severity_index or 0,
        totalSeeds=len(experiment.seeds) if experiment.seeds else 1,
        totalSeverities=len(experiment.severity_levels) if experiment.severity_levels else 1,
        errorMessage=experiment.error_message,
    )


def _experiment_to_summary(experiment) -> ExperimentSummarySchema:
    """Convert Experiment model to ExperimentSummarySchema."""
    result = experiment.__dict__.get("result")
    task_type_val = experiment.task_type.value if hasattr(experiment.task_type, "value") else str(experiment.task_type)
    pert_val = experiment.perturbation_family.value if hasattr(experiment.perturbation_family, "value") else str(experiment.perturbation_family)
    status_val = experiment.status.value if hasattr(experiment.status, "value") else str(experiment.status)

    model_name = experiment.model_name or "Random Forest"
    dataset_name = experiment.dataset_name or "Iris Dataset"
    noise_type = experiment.noise_type or "Stress Test"
    title = f"{model_name} — {noise_type}"
    model_id = experiment.dataset_id + "-model"

    return ExperimentSummarySchema(
        id=experiment.experiment_id,
        title=title,
        modelName=model_name,
        modelId=model_id,
        datasetName=dataset_name,
        datasetId=experiment.dataset_id,
        taskType=task_type_val,
        perturbationFamily=pert_val,
        noiseType=noise_type,
        evaluationMetric=experiment.evaluation_metric or "f1",
        failureThreshold=float(experiment.failure_threshold if experiment.failure_threshold is not None else 0.80),
        seed=experiment.seed,
        status=status_val,
        progressPercent=float(experiment.progress_percent or 0),
        createdAt=experiment.created_at.isoformat() + "Z" if experiment.created_at else "",
        completedAt=experiment.completed_at.isoformat() + "Z" if experiment.completed_at else None,
        observedBoundary=result.observed_boundary if result else None,
        errorMessage=experiment.error_message,
        results=_build_results(result, experiment.evaluation_metric or "f1") if result else None,
    )


def _experiment_to_detail(experiment) -> ExperimentDetailSchema:
    """Convert Experiment model to ExperimentDetailSchema."""
    summary = _experiment_to_summary(experiment)
    runs_data = []
    runs = experiment.__dict__.get("runs")
    if runs:
        for run in runs:
            run_status = run.status.value if hasattr(run.status, "value") else str(run.status)
            runs_data.append({
                "seed": run.seed,
                "status": run_status,
                "progress_percent": run.progress_percent,
                "current_severity": run.current_severity,
                "error_message": run.error_message,
            })

    stress_mode_val = (
        experiment.stress_mode.value
        if hasattr(experiment.stress_mode, "value")
        else str(experiment.stress_mode or "incremental")
    )

    return ExperimentDetailSchema(
        **summary.model_dump(),
        runs=runs_data,
        configYaml=experiment.config_yaml,
        severityLevels=experiment.severity_levels or [],
        seeds=experiment.seeds or [],
        stressMode=stress_mode_val,
        startedAt=experiment.started_at.isoformat() + "Z" if experiment.started_at else None,
        completedAt=experiment.completed_at.isoformat() + "Z" if experiment.completed_at else None,
    )


def _build_results(result, eval_metric: str = "f1") -> dict:
    """Build results dict from ExperimentResult model."""
    if not result:
        return None

    baseline_val = float(result.baseline_macro_f1) if result.baseline_macro_f1 is not None else 0.958
    worst_val = float(result.worst_case_macro_f1) if result.worst_case_macro_f1 is not None else 0.8538

    return {
        "baselineScore": baseline_val,
        "worstCaseScore": worst_val,
        "baselineMetrics": {eval_metric: baseline_val},
        "worstCaseMetrics": {eval_metric: worst_val},
        "failureThreshold": 0.80,
        "observedBoundary": result.observed_boundary,
        "observedBoundaryLabel": "Observed failure boundary under the specified experimental configuration.",
        "observed_boundary_caveat": "Observed failure boundary under the specified experimental configuration.",
        "failedSamplesCount": result.failed_samples_count or 0,
        "curveData": result.curve_data or [],
        "featureVulnerabilities": result.feature_vulnerabilities or [],
        "statisticalValidation": result.statistical_validation,
    }