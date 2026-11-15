"""Model adapter endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.repositories.model_adapter import ModelAdapterRepository
from app.schemas import ModelAdapterSchema

router = APIRouter()

# Real scikit-learn adapters supported by scripts/experiments/run_generic.py.
# Generic choices work with custom datasets, unlike benchmark-specific DB rows.
# They are adapter configurations, NOT trained or calibrated models.
GENERIC_MODELS = (
    {"id": "generic-rf-classifier", "name": "Random Forest Classifier", "taskType": "classification", "predictProba": True,
     "description": "Random forest trained from scratch on the selected dataset.", "parameters": {"n_estimators": 100, "max_depth": 12}},
    {"id": "generic-logistic-regression", "name": "Logistic Regression", "taskType": "classification", "predictProba": True,
     "description": "Regularized logistic classifier.", "parameters": {"C": 1.0, "max_iter": 500}},
    {"id": "generic-gradient-boosting-classifier", "name": "Gradient Boosting Classifier", "taskType": "classification", "predictProba": True,
     "description": "Gradient boosted decision trees.", "parameters": {"n_estimators": 100, "learning_rate": 0.1}},
    {"id": "generic-svc-classifier", "name": "Support Vector Classifier (SVC)", "taskType": "classification", "predictProba": True,
     "description": "RBF support vector classifier with estimated probabilities.", "parameters": {"C": 1.0}},
    {"id": "generic-rf-regressor", "name": "Random Forest Regressor", "taskType": "regression", "predictProba": False,
     "description": "Random forest for continuous targets.", "parameters": {"n_estimators": 100, "max_depth": 12}},
    {"id": "generic-ridge-regression", "name": "Ridge Regression", "taskType": "regression", "predictProba": False,
     "description": "L2-regularized linear regression.", "parameters": {"alpha": 1.0}},
    {"id": "generic-linear-regression", "name": "Linear Regression", "taskType": "regression", "predictProba": False,
     "description": "Ordinary least squares regression.", "parameters": {}},
    {"id": "generic-gradient-boosting-regressor", "name": "Gradient Boosting Regressor", "taskType": "regression", "predictProba": False,
     "description": "Gradient boosted regression trees.", "parameters": {"n_estimators": 100, "learning_rate": 0.1}},
)


def _generic_schema(spec: dict) -> ModelAdapterSchema:
    return ModelAdapterSchema(
        id=spec["id"],
        name=spec["name"],
        description=spec["description"],
        taskType=spec["taskType"],
        taskTypes=[spec["taskType"]],
        supportedDatasets=[],
        framework="scikit-learn",
        predictProba=spec["predictProba"],
        parameters=spec["parameters"],
    )



@router.get("", response_model=List[ModelAdapterSchema])
async def list_models(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    session: AsyncSession = Depends(get_session),
) -> List[ModelAdapterSchema]:
    """List supported pre-configured model adapters."""
    repo = ModelAdapterRepository(session)

    # Catalog GET is read-only; benchmark seeds are populated by a separate setup step.
    if dataset_id:
        models = await repo.get_by_dataset(dataset_id)
    else:
        models = await repo.get_active()

    catalog = [_model_to_schema(m) for m in models]
    catalog.extend(_generic_schema(spec) for spec in GENERIC_MODELS)
    return catalog


@router.get("/{model_id}", response_model=ModelAdapterSchema)
async def get_model(
    model_id: str,
    session: AsyncSession = Depends(get_session),
) -> ModelAdapterSchema:
    """Get a specific model adapter by ID."""
    for spec in GENERIC_MODELS:
        if spec["id"] == model_id:
            return _generic_schema(spec)

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
        taskTypes=[model.task_type] if model.task_type else ["classification"],
        supportedDatasets=[model.dataset_id],
        framework=model.framework,
        baselineF1=model.baseline_f1,
        baselineAccuracy=model.baseline_accuracy,
        predictProba=True,
        parameters=model.hyperparameters or {},
    )