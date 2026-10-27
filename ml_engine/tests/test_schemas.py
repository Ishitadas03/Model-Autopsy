"""Comprehensive unit and integration tests for Model Autopsy Pydantic v2 schemas."""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from model_autopsy.analysis.failure_boundary import FailureBoundaryResult
from model_autopsy.analysis.statistical import SampleStatistics, SeverityAggregateStatistics
from model_autopsy.metrics.evaluator import EvaluationMetrics
from model_autopsy.schemas import (
    ApiErrorResponse,
    ArtifactManifestSchema,
    CorruptionAggregateResultSchema,
    DatasetSchema,
    EvaluationMetricsSchema,
    ExperimentCancelResponse,
    ExperimentDetailSchema,
    ExperimentProgressSchema,
    ExperimentRunRequest,
    ExperimentSummarySchema,
    FailureBoundarySchema,
    MetricStatisticsSchema,
    MetricType,
    ModelAdapterSchema,
    RunStatus,
    SeverityAggregatePointSchema,
    StressConfigSchema,
    StressMode,
    StressType,
    TaskType,
    ValidationErrorItem,
)


def test_dataclass_to_evaluation_metrics_schema():
    """Verify conversion of EvaluationMetrics dataclass to Pydantic schema."""
    raw_metric = EvaluationMetrics(
        macro_f1=0.8538,
        accuracy=0.8667,
        per_class_f1=[1.0, 0.8421, 0.8571],
        per_class_precision=[1.0, 0.8889, 0.8182],
        per_class_recall=[1.0, 0.8, 0.9],
        confusion_matrix=[[10, 0, 0], [0, 8, 2], [0, 1, 9]],
        absolute_degradation_pp=7.28,
        relative_degradation_pct=7.80,
        is_failed=False,
        rel_drop_exceeds_15_pct=False,
    )

    schema = EvaluationMetricsSchema.model_validate(raw_metric)
    assert schema.macro_f1 == 0.8538
    assert schema.accuracy == 0.8667
    assert schema.is_failed is False
    assert schema.confusion_matrix[0] == [10, 0, 0]

    # Verify serialization
    data = schema.model_dump()
    assert data["macro_f1"] == 0.8538


def test_dataclass_to_metric_statistics_schema():
    """Verify conversion of SampleStatistics dataclass to MetricStatisticsSchema."""
    stats = SampleStatistics(
        n=5,
        mean=0.9265,
        sample_std=0.0280,
        sem=0.0125,
        df=4,
        t_critical=2.7764,
        margin_of_error=0.0347,
        ci_lower=0.8918,
        ci_upper=0.9612,
    )

    schema = MetricStatisticsSchema.model_validate(stats)
    assert schema.n == 5
    assert schema.df == 4
    assert schema.mean == 0.9265
    assert schema.ci_lower == 0.8918


def test_dataclass_to_failure_boundary_schema():
    """Verify conversion of FailureBoundaryResult dataclass to FailureBoundarySchema."""
    fb_res = FailureBoundaryResult(
        observed_boundary=0.25,
        is_boundary_observed=True,
        threshold=0.80,
        tested_severities=[0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3],
        boundary_caption="Observed failure boundary under the specified experimental configuration.",
        summary_message="Observed failure boundary at s = 0.25.",
    )

    schema = FailureBoundarySchema.model_validate(fb_res)
    assert schema.observed_boundary == 0.25
    assert schema.is_boundary_observed is True
    assert "Observed failure boundary" in schema.boundary_caption


def test_cell_based_progress_calculation():
    """Verify that ExperimentProgressSchema calculates percent based strictly on cells."""
    # 1. Automatic calculation
    progress = ExperimentProgressSchema(
        completed_cells=75,
        total_cells=315,
        current_model="random_forest",
        current_severity=0.15,
    )
    expected_pct = round((75 / 315) * 100.0, 2)
    assert progress.percent_complete == expected_pct

    # 2. Complete status
    progress_full = ExperimentProgressSchema(completed_cells=315, total_cells=315)
    assert progress_full.percent_complete == 100.0


def test_experiment_run_request_validation():
    """Verify validation rules and alias handling on experiment run requests."""
    # Valid camelCase payload from frontend
    valid_camel = {
        "datasetId": "iris",
        "modelId": "logistic_regression",
        "stressConfig": {
            "type": "gaussian_noise",
            "severityLevels": [0.0, 0.1, 0.2, 0.3],
            "mode": "random",
        },
        "metric": "f1",
        "failureThreshold": 0.80,
        "testSize": 0.20,
        "seeds": [42, 123],
    }

    req = ExperimentRunRequest.model_validate(valid_camel)
    assert req.dataset_id == "iris"
    assert req.model_id == "logistic_regression"
    assert req.stress_config.type == StressType.GAUSSIAN_NOISE
    assert req.stress_config.mode == StressMode.RANDOM
    assert req.failure_threshold == 0.80

    # Invalid threshold (> 1.0)
    invalid_threshold = valid_camel.copy()
    invalid_threshold["failureThreshold"] = 1.50
    with pytest.raises(ValidationError):
        ExperimentRunRequest.model_validate(invalid_threshold)

    # Empty severities
    invalid_severities = valid_camel.copy()
    invalid_severities["stressConfig"] = {"type": "missingness", "severityLevels": []}
    with pytest.raises(ValidationError):
        ExperimentRunRequest.model_validate(invalid_severities)


def test_canonical_manifest_schema_parsing():
    """Verify parsing real canonical manifest.json from E003."""
    manifest_path = Path("artifacts/experiments/E003/manifest.json")
    assert manifest_path.exists(), "E003 manifest.json must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    manifest_schema = ArtifactManifestSchema.model_validate(data)
    assert manifest_schema.experiment_id == "E003"
    assert manifest_schema.protocol_version == "1.0.0"
    assert manifest_schema.environment.python_version == "3.13.5"
    assert "numpy" in manifest_schema.environment.package_versions


def test_canonical_e003_aggregate_parsing():
    """Verify parsing real canonical aggregate_comparison.json from E003."""
    agg_path = Path("artifacts/experiments/E003/aggregate_comparison.json")
    assert agg_path.exists(), "E003 aggregate_comparison.json must exist"

    with open(agg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rf_gaussian = data["models"]["random_forest"]["corruptions"]["gaussian_noise"]
    corr_schema = CorruptionAggregateResultSchema.model_validate(rf_gaussian)

    assert corr_schema.experiment_id == "E001"
    assert corr_schema.n_successful_seeds == 5
    assert len(corr_schema.severity_aggregates) == 7
    assert corr_schema.severity_aggregates[0].macro_f1.mean == 0.9265


def test_api_error_response_structure():
    """Verify API error response envelope serialization."""
    err = ApiErrorResponse(
        error="Not Found",
        code="EXPERIMENT_NOT_FOUND",
        detail="Experiment E999 does not exist.",
        experiment_id="E999",
        validation_errors=[
            ValidationErrorItem(
                loc=["path", "experiment_id"],
                msg="Experiment ID not found",
                type="not_found",
            )
        ],
    )

    dump = err.model_dump()
    assert dump["code"] == "EXPERIMENT_NOT_FOUND"
    assert dump["experiment_id"] == "E999"
    assert len(dump["validation_errors"]) == 1


def test_backend_schemas_reexport_identity():
    """Verify that backend/app/schemas re-exports the exact canonical schemas."""
    import sys

    repo_root = Path(__file__).resolve().parent.parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    import backend.app.schemas as backend_schemas
    import model_autopsy.schemas as ml_schemas

    assert backend_schemas.ExperimentRunRequest is ml_schemas.ExperimentRunRequest
    assert backend_schemas.ExperimentSummarySchema is ml_schemas.ExperimentSummarySchema
    assert backend_schemas.EvaluationMetricsSchema is ml_schemas.EvaluationMetricsSchema
    assert backend_schemas.ApiErrorResponse is ml_schemas.ApiErrorResponse
