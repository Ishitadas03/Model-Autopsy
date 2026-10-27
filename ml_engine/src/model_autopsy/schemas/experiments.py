"""Experiment execution, lifecycle tracking, and progress schemas for Model Autopsy."""

from typing import Any, Dict, List, Optional
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

    @model_validator(mode="before")
    @classmethod
    def calculate_percent(cls, data: Any) -> Any:
        """Ensure percent_complete matches cell counts deterministically."""
        if isinstance(data, dict):
            completed = data.get("completed_cells", data.get("completedCells", 0))
            total = data.get("total_cells", data.get("totalCells", 1))
            if total > 0 and "percent_complete" not in data and "percentComplete" not in data:
                data["percent_complete"] = round((completed / total) * 100.0, 2)
        return data


class ExperimentRunRequest(SchemaBase):
    """Submission payload to initiate a reproducible experiment run."""

    dataset_id: str = Field(
        default="iris",
        alias="datasetId",
        description="Identifier of benchmark dataset to evaluate.",
    )
    model_id: str = Field(
        default="random_forest",
        alias="modelId",
        description="Identifier of model architecture to evaluate.",
    )
    stress_config: StressConfigSchema = Field(
        alias="stressConfig",
        description="Perturbation family and severity sweep specification.",
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
    seeds: List[int] = Field(
        default_factory=lambda: [42, 123, 456, 789, 1011],
        min_length=1,
        description="List of PRNG research seeds for multi-seed statistical evaluation.",
    )
    title: Optional[str] = Field(
        default=None,
        description="Optional human-readable title for the experiment run.",
    )


class ExperimentSummarySchema(SchemaBase):
    """Concise experiment run overview for catalog and dashboard listings."""

    id: str = Field(description="Unique experiment execution ID (e.g. E001, E003, EXP-001).")
    title: str = Field(description="Human-readable title.")
    dataset_id: str = Field(alias="datasetId", description="Evaluated dataset identifier.")
    dataset_name: str = Field(alias="datasetName", description="Evaluated dataset display name.")
    model_id: str = Field(alias="modelId", description="Evaluated model adapter identifier.")
    model_name: str = Field(alias="modelName", description="Evaluated model display name.")
    task_type: TaskType = Field(alias="taskType", description="Machine learning task type.")
    metric: MetricType = Field(description="Primary evaluation metric.")
    failure_threshold: float = Field(
        alias="failureThreshold",
        description="Pre-registered failure threshold.",
    )
    status: RunStatus = Field(description="Current execution lifecycle status.")
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


class ExperimentDetailSchema(ExperimentSummarySchema):
    """Detailed experiment run representation with results, config, and artifacts."""

    stress_config: StressConfigSchema = Field(
        alias="stressConfig",
        description="Active perturbation parameters.",
    )
    test_size: float = Field(
        default=0.20,
        alias="testSize",
        description="Evaluation partition proportion.",
    )
    seeds: List[int] = Field(
        default_factory=lambda: [42],
        description="Evaluated PRNG seeds.",
    )
    progress: Optional[ExperimentProgressSchema] = Field(
        default=None,
        description="Fine-grained cell progress tracking.",
    )
    results: Optional[ExperimentResultsSchema] = Field(
        default=None,
        description="Structured evaluation results, curves, and boundary findings.",
    )
    artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of artifact logical keys to relative filesystem paths.",
    )


class ExperimentCancelResponse(SchemaBase):
    """Response payload following an experiment cancellation request."""

    experiment_id: str = Field(
        alias="experimentId",
        description="Identifier of the cancelled experiment.",
    )
    status: RunStatus = Field(description="Updated experiment status (CANCELLED).")
    message: str = Field(description="Descriptive message detailing cancellation outcome.")
    terminated_pid: Optional[int] = Field(
        default=None,
        alias="terminatedPid",
        description="Operating system process ID terminated, if applicable.",
    )
    confirmed_stopped: bool = Field(
        alias="confirmedStopped",
        description="Whether process termination was verified prior to response.",
    )
