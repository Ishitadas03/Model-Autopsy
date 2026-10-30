"""Backend application schemas re-exported and extended from canonical ML Engine contracts.

The ML engine owns all domain and evaluation schemas to ensure single-source-of-truth
integrity across training, offline experiments, and online API serving.
These models ensure seamless serialization and compatibility with frontend-api-contract.md.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

# Re-export core enums and schemas from model_autopsy
from model_autopsy.schemas import (
    ApiErrorResponse,
    ArtifactManifestSchema,
    ArtifactReferenceSchema,
    CorruptionAggregateResultSchema,
    CurvePointSchema,
    DatasetFeatureSchema,
    EnvironmentMetadataSchema,
    EvaluationMetricsSchema,
    FailureBoundarySchema,
    MetricStatisticsSchema,
    MetricType,
    MostVulnerableFeatureSchema,
    RunStatus,
    SchemaBase,
    SeverityAggregatePointSchema,
    StatisticalValidationSchema,
    StressConfigSchema,
    StressMode,
    StressType,
    TaskType,
    ValidationErrorItem,
)


# ==========================================
# Frontend API Contract Compliant Schemas
# ==========================================

class FailedSample(BaseModel):
    """Failed sample instance with clean and stressed feature values."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    sample_index: int = Field(alias="sampleIndex")
    true_label: Any = Field(alias="trueLabel")
    predicted_label: Any = Field(alias="predictedLabel")
    confidence: float
    noise_level: Optional[float] = Field(default=None, alias="noiseLevel")
    severity: Optional[float] = None
    stress_type: Optional[str] = Field(default=None, alias="stressType")
    features: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class FailedSamplesResponse(BaseModel):
    """Paginated failed samples response."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    total: int
    samples: List[FailedSample]


class DatasetSchema(BaseModel):
    """Dataset catalog schema compatible with API contract."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    name: str
    description: Optional[str] = ""
    task_type: str = Field(alias="taskType")
    sample_count: int = Field(alias="sampleCount")
    feature_count: int = Field(alias="featureCount")
    class_count: Optional[int] = Field(default=None, alias="classCount")
    license: Optional[str] = "CC-BY-4.0"
    tags: List[str] = Field(default_factory=list)
    is_custom: bool = Field(default=False, alias="isCustom")
    features: List[Any] = Field(default_factory=list)


class ModelAdapterSchema(BaseModel):
    """Model adapter catalog schema compatible with API contract."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    name: str
    description: Optional[str] = ""
    task_type: Optional[str] = Field(default="classification", alias="taskType")
    task_types: List[str] = Field(default_factory=lambda: ["classification"], alias="taskTypes")
    supported_datasets: List[str] = Field(default_factory=list, alias="supportedDatasets")
    framework: str = "scikit-learn"
    baseline_f1: Optional[float] = Field(default=None, alias="baselineF1")
    baseline_accuracy: Optional[float] = Field(default=None, alias="baselineAccuracy")
    predict_proba: bool = Field(default=True, alias="predictProba")
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ExperimentCurvePoint(BaseModel):
    """Data point along the robustness degradation curve."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    noise_level: Optional[float] = Field(default=None, alias="noiseLevel")
    severity: Optional[float] = None
    score: Optional[float] = None
    f1: Optional[float] = None
    accuracy: Optional[float] = None
    mae: Optional[float] = None
    rmse: Optional[float] = None
    baseline: Optional[float] = None
    threshold: Optional[float] = None


class FeatureVulnerability(BaseModel):
    """Individual feature vulnerability indicator with required scientific caveat."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    feature: str
    drop: Optional[float] = None
    relative_change_percent: Optional[float] = Field(default=None, alias="relativeChangePercent")
    rank: Optional[int] = None
    caveat: str = "Empirical sensitivity — not a causal explanation."


class ExperimentResultsResponse(BaseModel):
    """Experiment results structure matching frontend contract."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    baseline_score: Optional[float] = Field(default=None, alias="baselineScore")
    worst_case_score: Optional[float] = Field(default=None, alias="worstCaseScore")
    baseline_metrics: Optional[Dict[str, float]] = Field(default_factory=dict, alias="baselineMetrics")
    worst_case_metrics: Optional[Dict[str, float]] = Field(default_factory=dict, alias="worstCaseMetrics")
    failure_threshold: Optional[float] = Field(default=None, alias="failureThreshold")
    observed_boundary: Optional[float] = Field(default=None, alias="observedBoundary")
    observed_boundary_label: str = Field(
        default="Observed failure boundary under the specified experimental configuration.",
        alias="observedBoundaryLabel",
    )
    observed_boundary_caveat: Optional[str] = Field(
        default="Observed failure boundary under the specified experimental configuration.",
        alias="observed_boundary_caveat",
    )
    failed_samples_count: int = Field(default=0, alias="failedSamplesCount")
    curve_data: List[Dict[str, Any]] = Field(default_factory=list, alias="curveData")
    feature_vulnerabilities: List[Dict[str, Any]] = Field(default_factory=list, alias="featureVulnerabilities")
    statistical_validation: Optional[Dict[str, Any]] = Field(default=None, alias="statisticalValidation")
    most_vulnerable_feature: Optional[Dict[str, Any]] = Field(default=None, alias="mostVulnerableFeature")


class ExperimentSummarySchema(BaseModel):
    """Summary representation for experiment listing."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    title: Optional[str] = None
    model_name: str = Field(alias="modelName")
    model_id: Optional[str] = Field(default=None, alias="modelId")
    dataset_name: str = Field(alias="datasetName")
    dataset_id: str = Field(alias="datasetId")
    task_type: str = Field(alias="taskType")
    perturbation_family: Optional[str] = Field(default=None, alias="perturbationFamily")
    noise_type: Optional[str] = Field(default=None, alias="noiseType")
    evaluation_metric: Optional[str] = Field(default=None, alias="evaluationMetric")
    metric: Optional[str] = None
    failure_threshold: float = Field(alias="failureThreshold")
    seed: int = 42
    status: str = "queued"
    progress_percent: float = Field(default=0.0, alias="progressPercent")
    created_at: str = Field(alias="createdAt")
    completed_at: Optional[str] = Field(default=None, alias="completedAt")
    observed_boundary: Optional[float] = Field(default=None, alias="observedBoundary")
    error_message: Optional[str] = Field(default=None, alias="errorMessage")
    results: Optional[ExperimentResultsResponse] = None


class ExperimentDetailSchema(ExperimentSummarySchema):
    """Detailed experiment representation."""
    runs: List[Dict[str, Any]] = Field(default_factory=list)
    config_yaml: Optional[str] = Field(default=None, alias="configYaml")
    severity_levels: List[float] = Field(default_factory=list, alias="severityLevels")
    seeds: List[int] = Field(default_factory=list)
    stress_mode: Optional[str] = Field(default=None, alias="stressMode")
    stress_config: Optional[Dict[str, Any]] = Field(default=None, alias="stressConfig")
    test_size: Optional[float] = Field(default=0.20, alias="testSize")
    progress: Optional[Dict[str, Any]] = None
    artifacts: Union[Dict[str, str], List[Dict[str, Any]]] = Field(default_factory=dict)


class ExperimentRunRequest(BaseModel):
    """Request payload to create a new experiment."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    model_name: Optional[str] = Field(default=None, alias="modelName")
    model_id: Optional[str] = Field(default=None, alias="modelId")
    dataset_name: Optional[str] = Field(default=None, alias="datasetName")
    dataset_id: str = Field(alias="datasetId")
    task_type: Optional[str] = Field(default="classification", alias="taskType")
    perturbation_family: Optional[str] = Field(default="gaussian_noise", alias="perturbationFamily")
    noise_type: Optional[str] = Field(default="Gaussian Noise", alias="noiseType")
    evaluation_metric: Optional[str] = Field(default="f1", alias="evaluationMetric")
    metric: Optional[str] = None
    failure_threshold: float = Field(default=0.80, alias="failureThreshold")
    seed: int = 42
    seeds: Optional[List[int]] = None
    stress_mode: Optional[str] = Field(default="incremental", alias="stressMode")
    stress_config: Optional[Any] = Field(default=None, alias="stressConfig")
    test_size: Optional[float] = Field(default=0.20, alias="testSize")
    title: Optional[str] = None


class ExperimentCancelResponse(BaseModel):
    """Response payload when cancelling an experiment."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    success: bool = True
    experiment_id: Optional[str] = Field(default=None, alias="experimentId")
    status: Optional[str] = "cancelled"
    message: Optional[str] = "Experiment cancelled successfully"


class ExperimentProgressSchema(BaseModel):
    """Progress tracking payload."""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    experiment_id: Optional[str] = Field(default=None, alias="experimentId")
    status: str = "queued"
    progress_percent: float = Field(default=0.0, alias="progressPercent")
    completed_cells: int = Field(default=0, alias="completedCells")
    total_cells: int = Field(default=1, alias="totalCells")
    current_seed_index: int = Field(default=0, alias="currentSeedIndex")
    current_severity_index: int = Field(default=0, alias="currentSeverityIndex")
    current_seed: Optional[int] = Field(default=None, alias="currentSeed")
    current_severity: Optional[float] = Field(default=None, alias="currentSeverity")
    current_model: Optional[str] = Field(default=None, alias="currentModel")
    current_corruption: Optional[str] = Field(default=None, alias="currentCorruption")
    total_seeds: int = Field(default=1, alias="totalSeeds")
    total_severities: int = Field(default=1, alias="totalSeverities")
    error_message: Optional[str] = Field(default=None, alias="errorMessage")


# Set backward-compatible alias
ExperimentResultsSchema = ExperimentResultsResponse

__all__ = [
    # Base
    "SchemaBase",
    # Enums
    "TaskType",
    "MetricType",
    "StressType",
    "RunStatus",
    "StressMode",
    # Catalog
    "DatasetFeatureSchema",
    "DatasetSchema",
    "ModelAdapterSchema",
    # Metrics & Evaluation
    "EvaluationMetricsSchema",
    "MetricStatisticsSchema",
    "SeverityAggregatePointSchema",
    "FailureBoundarySchema",
    "CorruptionAggregateResultSchema",
    "CurvePointSchema",
    "StatisticalValidationSchema",
    "MostVulnerableFeatureSchema",
    "ExperimentResultsSchema",
    "ExperimentResultsResponse",
    "ExperimentCurvePoint",
    "FeatureVulnerability",
    # Experiment Execution & Lifecycle
    "StressConfigSchema",
    "ExperimentProgressSchema",
    "ExperimentRunRequest",
    "ExperimentSummarySchema",
    "ExperimentDetailSchema",
    "ExperimentCancelResponse",
    # Artifacts & Manifests
    "ArtifactReferenceSchema",
    "EnvironmentMetadataSchema",
    "ArtifactManifestSchema",
    # Error Envelopes
    "ValidationErrorItem",
    "ApiErrorResponse",
    # Failures
    "FailedSample",
    "FailedSamplesResponse",
]
