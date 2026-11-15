"""Bound expensive model hyperparameters before training on Render Free."""
import math

import pytest

from app.services.model_limits import validate_model_params
from app.services.baseline_service import baseline_service


@pytest.mark.parametrize("name,task,params", [
    ("Random Forest Classifier", "classification", {"n_estimators": 100000}),
    ("Random Forest Regressor", "regression", {"max_depth": 1000}),
    ("Logistic Regression", "classification", {"max_iter": 100000}),
    ("Gradient Boosting Classifier", "classification", {"learning_rate": math.inf}),
    ("Ridge Regression", "regression", {"alpha": float("nan")}),
    ("Random Forest Classifier", "classification", {"n_estimators": "100"}),
    ("Random Forest Classifier", "classification", {"n_estimators": 1.5}),
    ("Random Forest Classifier", "classification", {"arbitrary_knob": 999}),
    ("unsupported", "classification", {"n_estimators": 10}),
])
def test_reject_unbounded_or_unsupported_hyperparameters(name, task, params):
    with pytest.raises(ValueError):
        validate_model_params(name, task, params)


def test_valid_free_tier_parameters_and_reproducible_seed():
    params = validate_model_params(
        "Random Forest Classifier", "classification",
        {"n_estimators": 100, "max_depth": 10, "min_samples_split": 3, "random_state": 7},
    )
    assert params["n_estimators"] == 100
    model = baseline_service._instantiate_model(
        "generic-rf-classifier", True, seed=42, params=params
    )
    assert model.n_estimators == 100
    assert model.min_samples_split == 3
    assert model.random_state == 42  # Experiment seed always wins


def test_regression_params_are_applied_to_real_model():
    model = baseline_service._instantiate_model(
        "generic-gradient-boosting-regressor", False, seed=11,
        params={"n_estimators": 25, "learning_rate": 0.05, "max_depth": 4},
    )
    assert model.n_estimators == 25
    assert model.learning_rate == 0.05
    assert model.max_depth == 4


@pytest.mark.asyncio
async def test_api_rejects_expensive_experiment_before_enqueue(client, seed_datasets, seed_models):
    payload = {
        "modelName": "Random Forest Classifier",
        "datasetId": "iris",
        "taskType": "classification",
        "evaluationMetric": "f1",
        "failureThreshold": 0.7,
        "modelParams": {"n_estimators": 100000},
    }
    response = await client.post("/api/experiments", json=payload)
    assert response.status_code == 400, response.text
    assert "n_estimators" in response.text
