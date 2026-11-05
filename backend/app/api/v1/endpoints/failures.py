"""Failure samples endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.experiment import ExperimentRepository
from app.repositories.failure_sample import FailureSampleRepository
from app.schemas import FailedSample, ExperimentSummarySchema

router = APIRouter()


@router.get("/{experiment_id}/failures")
async def get_failed_samples(
    experiment_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    filter_class: Optional[str] = Query(None, alias="filterClass", description="Filter by ground truth or predicted class"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Retrieve paginated failed sample instances with feature values under clean vs. stressed states."""
    exp_repo = ExperimentRepository(session)
    fail_repo = FailureSampleRepository(session)

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

    samples, total = await fail_repo.get_by_experiment(
        experiment.id, page=page, page_size=limit, filter_class=filter_class
    )

    return {
        "total": total,
        "samples": [_sample_to_schema(s) for s in samples],
    }


def _sample_to_schema(sample) -> FailedSample:
    """Convert FailedSample model to FailedSample schema."""
    features = {}
    clean_dict = sample.features_clean or {}
    stressed_dict = sample.features_stressed or {}
    all_keys = set(clean_dict.keys()) | set(stressed_dict.keys())
    for feature_name in all_keys:
        features[feature_name] = {
            "clean": clean_dict.get(feature_name, 0),
            "stressed": stressed_dict.get(feature_name, 0),
        }

    return FailedSample(
        id=sample.sample_id,
        sampleIndex=sample.sample_index,
        trueLabel=sample.true_label,
        predictedLabel=sample.predicted_label,
        confidence=sample.confidence,
        noiseLevel=sample.noise_level,
        severity=sample.noise_level,
        features=features,
    )