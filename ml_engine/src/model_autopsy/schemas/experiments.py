"""Experiment execution, lifecycle tracking, and progress schemas for Model Autopsy."""

from typing import Any, Dict, List, Optional, Union
from pydantic import Field, model_validator

from model_autopsy.schemas.base import SchemaBase
from model_autopsy.schemas.enums import MetricType, RunStatus, StressMode, StressType, TaskType
from model_autopsy.schemas.metrics import ExperimentResultsSchema


class StressConfigSchema(SchemaBase):
    """Configuration for stress tests and perturbations."""

    type: StressType = Field(description="Perturbation family to apply.")
    severity_levels: List[float] = Field(
        alias="severityLevels",
        min_length=1,
        description="Discrete severity factors to evaluate (e.g. [0.0, 0.05, ..., 0.30]).",
    )
    mode: StressMode = Field(
        default=StressMode.RANDOM,
        description="Targeting mode: random isotropic, feature-specific, or structured.",
    )
    target_features: Optional[List[str]] = Field(
        default=None,
        alias="targetFeatures",
        description="Optional subset of feature names to perturb.",
    )


class ExperimentProgressSchema(SchemaBase):
    """Deterministic, cell-based execution progress tracking."""

    experiment_id: Optional[str] = Field(
        default=None,
        alias="experimentId",
        description="Associated experiment ID.",
    )
    status: Optional[str] = Field(
        default="queued",
        description="Current execution lifecycle status.",
    )
    completed_cells: int = Field(
        default=0,
        alias="completedCells",
        ge=0,
        description="Count of fully evaluated evaluation cells (model x corruption x severity x seed).",
    )
    total_cells: int = Field(
        default=1,
        alias="totalCells",
        gt=0,
        description="Total planned evaluation cells in the experimental grid.",
    )
    percent_complete: float = Field(
        default=0.0,
        alias="percentComplete",
        ge=0.0,
        le=100.0,
        description="Calculated cell completion percentage: (completed_cells / total_cells) * 100.",
    )
    progress_percent: Optional[float] = Field(
        default=0.0,
        alias="progressPercent",
        ge=0.0,
        le=100.0,
        description="Alternative alias for percent complete.",
    )
    current_model: Optional[str] = Field(
        default=None,
        alias="currentModel",
        description="Currently active model architecture ID.",
    )
    current_corruption: Optional[str] = Field(
        default=None,
        alias="currentCorruption",
        description="Currently active corruption modality ID.",
    )
    current_severity: Optional[float] = Field(
        default=None,
        alias="currentSeverity",
        description="Currently active severity level.",
    )
    current_seed: Optional[int] = Field(
        default=None,
        alias="currentSeed",
        description="Currently active PRNG seed.",
    )
    current_seed_index: int = Field(
        default=0,
        alias="currentSeedIndex",
    )
    current_severity_index: int = Field(
        default=0,
        alias="currentSeverityIndex",
    )
    total_seeds: int = Field(
        default=1,
        alias="totalSeeds",
    )
    total_severities: int = Field(
        default=1,
        alias="totalSeverities",
    )
    error_message: Optional[str] = Field(
        default=None,
        alias="errorMessage",
    )

    @model_validator(mode="before")
    @classmethod
    def calculate_percent(cls, data: Any) -> Any:
        """Ensure percent_complete and progress_percent match deterministically."""
        if isinstance(data, dict):
            completed = data.get("completed_cells", data.get("completedCells", 0))
            total = data.get("total_cells", data.get("totalCells", 1))
            pct = data.get("percent_complete") or data.get("percentComplete") or data.get("progress_percent") or data.get("progressPercent")
            if pct is not None:
                data["percent_complete"] = float(pct)
                data["progress_percent"] = float(pct)
            elif total > 0:
                calc = round((completed / total) * 100.0, 2)
                data["percent_complete"] = calc
                data["progress_percent"] = calc
        return data


class ExperimentRunRequest(SchemaBase):
    """Submission payload to initiate a reproducible experiment run."""

    dataset_id: str = Field(
        default="iris",
        alias="datasetId",
        description="Identifier of benchmark dataset to evaluate.",
    )
    dataset_name: Optional[str] = Field(
        default=None,
        alias="datasetName",
        description="Identifier of benchmark dataset to evaluate.",
    )
    model_id: Optional[str] = Field(
        default="random_forest",
        alias="modelId",
        description="Identifier of model architecture to evaluate.",
    )
    model_name: Optional[str] = Field(
        default=None,
        alias="modelName",
        description="Identifier of model architecture to evaluate.",
    )
    stress_config: Optional[StressConfigSchema] = Field(
        default=None,
        alias="stressConfig",
        description="Perturbation family and severity sweep specification.",
    )
    task_type: Optional[Union[TaskType, str]] = Field(
        default=TaskType.CLASSIFICATION,
        alias="taskType",
        description="Machine learning task type.",
    )
    perturbation_family: Optional[str] = Field(
        default=None,
        alias="perturbationFamily",
        description="Perturbation family name.",
    )
    noise_type: Optional[str] = Field(
        default=None,
        alias="noiseType",
        description="Noise type description.",
    )
    evaluation_metric: Optional[str] = Field(
        default=None,
        alias="evaluationMetric",
        description="Evaluation metric name.",
    )
    metric: MetricType = Field(
        default=MetricType.MACRO_F1,
        description="Primary metric for evaluating failure.",
    )
    failure_threshold: float = Field(
        default=0.80,
        alias="failureThreshold",
        ge=0.0,
        le=1.0,
        description="Strict threshold below which performance constitutes failure.",
    )
    test_size: float = Field(
        default=0.20,
        alias="testSize",
        gt=0.0,
        lt=1.0,
        description="Proportion of dataset reserved for evaluation partition.",
    )
    seed: Optional[int] = Field(
        default=42,
        description="Primary seed.",
    )
    seeds: Optional[List[int]] = Field(
        default=None,
        description="List of PRNG research seeds for multi-seed statistical evaluation.",
    )
    stress_mode: Optional[str] = Field(
        default=None,
        alias="stressMode",
        description="Stress mode (incremental, etc.).",
    )
    severity_levels: Optional[List[float]] = Field(
        default=None,
        alias="severityLevels",
        description="Direct severity levels list.",
    )
    title: Optional[str] = Field(
        default=None,
        description="Optional human-readable title for the experiment run.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # 1. Normalize model_id from modelName if model_id / modelId is missing
            if "modelId" not in data and "model_id" not in data and ("modelName" in data or "model_name" in data):
                data["model_id"] = data.get("modelName") or data.get("model_name")
            # 2. Normalize metric from evaluationMetric
            if "metric" not in data and ("evaluationMetric" in data or "evaluation_metric" in data):
                val = data.get("evaluationMetric") or data.get("evaluation_metric")
                data["metric"] = val
            # 3. If stressConfig is missing, construct it from flat fields if present
            if "stressConfig" not in data and "stress_config" not in data:
                p_family = data.get("perturbationFamily") or data.get("perturbation_family")
                severities = data.get("severityLevels") or data.get("severity_levels")
                mode_val = data.get("stressMode") or data.get("stress_mode") or "random"
                if p_family and severities is not None:
                    data["stress_config"] = {
                        "type": p_family,
                        "severityLevels": severities,
                        "mode": mode_val if mode_val in [e.value for e in StressMode] else "random",
                    }
        return data


class ExperimentSummarySchema(SchemaBase):
    """Concise experiment run overview for catalog and dashboard listings."""

    id: str = Field(description="Unique experiment execution ID (e.g. E001, E003, EXP-001).")
    title: Optional[str] = Field(default=None, description="Human-readable title.")
    dataset_id: str = Field(alias="datasetId", description="Evaluated dataset identifier.")
    dataset_name: Optional[str] = Field(default=None, alias="datasetName", description="Evaluated dataset display name.")
    model_id: Optional[str] = Field(default=None, alias="modelId", description="Evaluated model adapter identifier.")
    model_name: Optional[str] = Field(default=None, alias="modelName", description="Evaluated model display name.")
    task_type: Union[TaskType, str] = Field(default=TaskType.CLASSIFICATION, alias="taskType", description="Machine learning task type.")
    perturbation_family: Optional[str] = Field(default=None, alias="perturbationFamily", description="Perturbation family.")
    noise_type: Optional[str] = Field(default=None, alias="noiseType", description="Noise type.")
    evaluation_metric: Optional[str] = Field(default=None, alias="evaluationMetric", description="Evaluation metric.")
    metric: Optional[Union[MetricType, str]] = Field(default=MetricType.MACRO_F1, description="Primary evaluation metric.")
    failure_threshold: float = Field(
        default=0.80,
        alias="failureThreshold",
        description="Pre-registered failure threshold.",
    )
    seed: Optional[int] = Field(default=42, description="Primary seed.")
    status: Union[RunStatus, str] = Field(default=RunStatus.QUEUED, description="Current execution lifecycle status.")
    created_at: str = Field(alias="createdAt", description="UTC ISO timestamp of run creation.")
    completed_at: Optional[str] = Field(
        default=None,
        alias="completedAt",
        description="UTC ISO timestamp of run completion, if finished.",
    )
    progress_percent: float = Field(
        default=0.0,
        alias="progressPercent",
        ge=0.0,
        le=100.0,
        description="Execution progress percentage based on completed evaluation cells.",
    )
    observed_boundary: Optional[float] = Field(
        default=None,
        alias="observedBoundary",
        description="Empirical failure boundary, if observed.",
    )
    error_message: Optional[str] = Field(
        default=None,
        alias="errorMessage",
        description="Error detail message if status is failed.",
    )
    results: Optional[Any] = Field(
        default=None,
        description="Structured evaluation results, curves, and boundary findings.",
    )


class ExperimentDetailSchema(ExperimentSummarySchema):
    """Detailed experiment run representation with results, config, and artifacts."""

    stress_config: Optional[Any] = Field(
        default=None,
        alias="stressConfig",
        description="Active perturbation parameters.",
    )
    test_size: Optional[float] = Field(
        default=0.20,
        alias="testSize",
        description="Evaluation partition proportion.",
    )
    seeds: Optional[List[int]] = Field(
        default_factory=lambda: [42],
        description="Evaluated PRNG seeds.",
    )
    progress: Optional[Any] = Field(
        default=None,
        description="Fine-grained cell progress tracking.",
    )
    results: Optional[Any] = Field(
        default=None,
        description="Structured evaluation results, curves, and boundary findings.",
    )
    artifacts: Union[Dict[str, str], List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Map of artifact logical keys to relative filesystem paths.",
    )
    runs: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        description="Sub-runs telemetry data.",
    )
    config_yaml: Optional[str] = Field(
        default=None,
        alias="configYaml",
        description="Raw YAML configuration.",
    )
    severity_levels: Optional[List[float]] = Field(
        default_factory=list,
        alias="severityLevels",
        description="List of tested severities.",
    )
    stress_mode: Optional[str] = Field(
        default=None,
        alias="stressMode",
    )


class ExperimentCancelResponse(SchemaBase):
    """Response payload following an experiment cancellation request."""

    success: bool = Field(default=True, description="Whether cancellation succeeded.")
    experiment_id: str = Field(
        alias="experimentId",
        description="Identifier of the cancelled experiment.",
    )
    status: Union[RunStatus, str] = Field(default=RunStatus.CANCELLED, description="Updated experiment status (CANCELLED).")
    message: str = Field(default="Experiment cancelled successfully.", description="Descriptive message detailing cancellation outcome.")
    terminated_pid: Optional[int] = Field(
        default=None,
        alias="terminatedPid",
        description="Operating system process ID terminated, if applicable.",
    )
    confirmed_stopped: bool = Field(
        default=True,
        alias="confirmedStopped",
        description="Whether process termination was verified prior to response.",
    )
