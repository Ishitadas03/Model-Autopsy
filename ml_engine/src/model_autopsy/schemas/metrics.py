"""Statistical, metric, and degradation evaluation schemas for Model Autopsy."""

from typing import Any, Dict, List, Optional
from pydantic import Field

from model_autopsy.analysis.failure_boundary import MANDATED_BOUNDARY_CAPTION, MANDATED_SENSITIVITY_CAVEAT
from model_autopsy.schemas.base import SchemaBase


class EvaluationMetricsSchema(SchemaBase):
    """Schema representing atomic evaluation metrics from a single evaluation pass."""

    macro_f1: float = Field(ge=0.0, le=1.0, description="Macro-averaged F1 score.")
    accuracy: float = Field(ge=0.0, le=1.0, description="Overall classification accuracy.")
    per_class_f1: List[float] = Field(description="Per-class F1 scores.")
    per_class_precision: List[float] = Field(description="Per-class precision scores.")
    per_class_recall: List[float] = Field(description="Per-class recall scores.")
    confusion_matrix: List[List[int]] = Field(description="Confusion matrix integer counts.")
    absolute_degradation_pp: float = Field(
        description="Absolute degradation from baseline in percentage points."
    )
    relative_degradation_pct: float = Field(
        description="Relative degradation from baseline as percentage of clean capacity."
    )
    is_failed: bool = Field(description="Whether primary failure threshold was breached.")
    rel_drop_exceeds_15_pct: bool = Field(
        description="Diagnostic alert: relative degradation exceeded 15%."
    )


class MetricStatisticsSchema(SchemaBase):
    """Statistical dispersion and Student's t confidence interval parameters."""

    n: int = Field(gt=0, description="Number of independent seed evaluations.")
    mean: float = Field(description="Sample mean across evaluated seeds.")
    sample_std: float = Field(ge=0.0, description="Unbiased sample standard deviation (ddof=1).")
    sem: float = Field(ge=0.0, description="Standard error of the mean (sample_std / sqrt(n)).")
    df: int = Field(ge=1, description="Degrees of freedom (n - 1).")
    t_critical: float = Field(gt=0.0, description="Two-sided Student's t critical value.")
    margin_of_error: float = Field(ge=0.0, description="Margin of error (t_critical * sem).")
    ci_lower: float = Field(description="Lower bound of two-sided 95% confidence interval.")
    ci_upper: float = Field(description="Upper bound of two-sided 95% confidence interval.")


class SeverityAggregatePointSchema(SchemaBase):
    """Aggregate statistics for a single corruption severity level."""

    severity: float = Field(ge=0.0, description="Target perturbation severity factor.")
    n_successful_runs: int = Field(ge=0, description="Count of successfully executed seed runs.")
    n_failed_runs: int = Field(default=0, ge=0, description="Count of aborted seed runs.")
    macro_f1: MetricStatisticsSchema = Field(description="Macro-F1 sample statistics.")
    accuracy: MetricStatisticsSchema = Field(description="Accuracy sample statistics.")
    absolute_degradation_pp: MetricStatisticsSchema = Field(
        description="Absolute degradation sample statistics."
    )
    relative_degradation_pct: MetricStatisticsSchema = Field(
        description="Relative degradation sample statistics."
    )
    failure_count: int = Field(ge=0, description="Number of seeds breaching failure threshold.")
    failure_proportion: float = Field(
        ge=0.0, le=1.0, description="Proportion of seeds breaching failure threshold."
    )
    is_mean_failed: bool = Field(description="Whether sample mean breached failure threshold.")


class FailureBoundarySchema(SchemaBase):
    """Empirical failure boundary evaluation result."""

    observed_boundary: Optional[float] = Field(
        default=None,
        description="Earliest severity level where performance dropped below failure threshold.",
    )
    is_boundary_observed: bool = Field(
        description="Whether a boundary was observed within the tested severity sweep."
    )
    threshold: float = Field(description="Pre-registered reliability threshold.")
    tested_severities: List[float] = Field(description="Evaluated severity levels.")
    boundary_caption: str = Field(
        default=MANDATED_BOUNDARY_CAPTION,
        description="Mandatory scientific disclaimer caption.",
    )
    summary_message: str = Field(description="Human-readable boundary summary.")


class CorruptionAggregateResultSchema(SchemaBase):
    """Complete multi-seed aggregate evaluation for a model-corruption pair."""

    experiment_id: str = Field(description="Experiment identifier.")
    seeds: List[int] = Field(description="Evaluated PRNG seeds.")
    severities: List[float] = Field(description="Evaluated severity grid.")
    failure_threshold: float = Field(description="Pre-registered failure threshold.")
    n_total_seeds: int = Field(ge=1, description="Total seeds requested.")
    n_successful_seeds: int = Field(ge=0, description="Total seeds completed successfully.")
    n_failed_seeds: int = Field(default=0, ge=0, description="Total seeds failed.")
    failed_seed_details: List[Dict[str, Any]] = Field(default_factory=list)
    per_seed_results: Optional[Dict[str, Any]] = Field(
        default=None, description="Detailed per-seed records and confusion matrices."
    )
    per_seed_boundaries: Optional[Dict[str, Optional[float]]] = Field(
        default=None, description="Observed boundary for each individual seed."
    )
    severity_aggregates: List[SeverityAggregatePointSchema] = Field(
        description="Ordered sequence of severity statistics."
    )
    mean_observed_boundary: Optional[float] = Field(
        default=None, description="Earliest severity where mean Macro-F1 < threshold."
    )
    earliest_individual_boundary: Optional[float] = Field(
        default=None, description="Earliest severity where any seed Macro-F1 < threshold."
    )
    boundary_caption: str = Field(
        default=MANDATED_BOUNDARY_CAPTION,
        description="Mandatory scientific reporting caption.",
    )
    monotonicity_summary: Optional[Dict[str, Any]] = Field(default=None)


class CurvePointSchema(SchemaBase):
    """Single point along a frontend robustness visualization curve."""

    severity: float = Field(description="Perturbation severity.")
    f1: Optional[float] = Field(default=None, description="Macro-F1 score at this severity.")
    accuracy: Optional[float] = Field(default=None, description="Accuracy score at this severity.")
    baseline: float = Field(description="Unperturbed clean baseline metric.")
    threshold: float = Field(description="Failure boundary threshold.")


class StatisticalValidationSchema(SchemaBase):
    """Condensed multi-seed dispersion summary for frontend display."""

    num_seeds: int = Field(alias="numSeeds", ge=1, description="Number of evaluated seeds.")
    mean: float = Field(description="Mean metric score.")
    std: float = Field(ge=0.0, description="Sample standard deviation.")
    ci95: float = Field(ge=0.0, description="Half-width 95% margin of error.")


class MostVulnerableFeatureSchema(SchemaBase):
    """Most vulnerable feature indicator matching frontend schema."""

    name: str = Field(description="Name of the most sensitive feature.")
    degradation_pp: Optional[float] = Field(
        default=None,
        alias="degradationPp",
        description="Absolute degradation in percentage points.",
    )
    relative_change_percent: float = Field(
        alias="relativeChangePercent",
        description="Relative degradation percentage.",
    )
    caveat: str = Field(
        default=MANDATED_SENSITIVITY_CAVEAT,
        description="Mandatory scientific caveat caption.",
    )


class ExperimentResultsSchema(SchemaBase):
    """Comprehensive experiment result payload matching frontend/lib/schemas.ts."""

    baseline_metrics: Dict[str, float] = Field(
        alias="baselineMetrics",
        description="Clean baseline metrics dictionary.",
    )
    worst_case_metrics: Dict[str, float] = Field(
        alias="worstCaseMetrics",
        description="Metrics at maximum evaluated stress severity.",
    )
    failure_threshold: float = Field(
        alias="failureThreshold",
        description="Pre-registered failure threshold.",
    )
    observed_boundary: Optional[float] = Field(
        default=None,
        alias="observedBoundary",
        description="Empirical failure boundary.",
    )
    observed_boundary_label: str = Field(
        default=MANDATED_BOUNDARY_CAPTION,
        alias="observedBoundaryLabel",
        description="Mandatory scientific disclaimer.",
    )
    failed_samples_count: int = Field(
        default=0,
        alias="failedSamplesCount",
        description="Count of samples failing reliability criteria.",
    )
    statistical_validation: Optional[StatisticalValidationSchema] = Field(
        default=None,
        alias="statisticalValidation",
        description="Multi-seed statistical dispersion.",
    )
    most_vulnerable_feature: Optional[MostVulnerableFeatureSchema] = Field(
        default=None,
        alias="mostVulnerableFeature",
        description="Identified most sensitive feature, if applicable.",
    )
    curve_data: List[CurvePointSchema] = Field(
        default_factory=list,
        alias="curveData",
        description="Ordered points for robustness curve plotting.",
    )
