"""Canonical Pydantic v2 schemas and API integration contracts for Model Autopsy."""

from model_autopsy.schemas.artifacts import (
    ArtifactManifestSchema,
    ArtifactReferenceSchema,
    EnvironmentMetadataSchema,
)
from model_autopsy.schemas.base import SchemaBase
from model_autopsy.schemas.catalog import (
    DatasetFeatureSchema,
    DatasetSchema,
    ModelAdapterSchema,
)
from model_autopsy.schemas.enums import (
    MetricType,
    RunStatus,
    StressMode,
    StressType,
    TaskType,
)
from model_autopsy.schemas.errors import (
    ApiErrorResponse,
    ValidationErrorItem,
)
from model_autopsy.schemas.experiments import (
    ExperimentCancelResponse,
    ExperimentDetailSchema,
    ExperimentProgressSchema,
    ExperimentRunRequest,
    ExperimentSummarySchema,
    StressConfigSchema,
)
from model_autopsy.schemas.metrics import (
    CorruptionAggregateResultSchema,
    CurvePointSchema,
    EvaluationMetricsSchema,
    ExperimentResultsSchema,
    FailureBoundarySchema,
    MetricStatisticsSchema,
    MostVulnerableFeatureSchema,
    SeverityAggregatePointSchema,
    StatisticalValidationSchema,
)

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
]
