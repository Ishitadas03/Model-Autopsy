from pathlib import Path

content = '''"""Backend application schemas re-exported and extended from canonical ML Engine contracts.

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
    ExperimentCancelResponse,
    ExperimentDetailSchema,
    ExperimentProgressSchema,
    ExperimentResultsSchema,
    ExperimentRunRequest,
    ExperimentSummarySchema,
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
'''

Path("backend/app/schemas/__init__.py").write_text(content, encoding="utf-8")
print("Successfully updated backend/app/schemas/__init__.py")

