"""Analysis, failure boundary, and statistical modules for Model Autopsy."""

from model_autopsy.analysis.failure_boundary import (
    MANDATED_BOUNDARY_CAPTION,
    MANDATED_SENSITIVITY_CAVEAT,
    FailureBoundaryResult,
    compute_feature_vulnerabilities,
    detect_failure_boundary,
)
from model_autopsy.analysis.statistical import (
    MultiSeedEvaluationResult,
    SampleStatistics,
    SeverityAggregateStatistics,
    aggregate_multi_seed_results,
    compute_sample_statistics,
)

__all__ = [
    "FailureBoundaryResult",
    "detect_failure_boundary",
    "compute_feature_vulnerabilities",
    "MANDATED_BOUNDARY_CAPTION",
    "MANDATED_SENSITIVITY_CAVEAT",
    "SampleStatistics",
    "SeverityAggregateStatistics",
    "MultiSeedEvaluationResult",
    "compute_sample_statistics",
    "aggregate_multi_seed_results",
]
