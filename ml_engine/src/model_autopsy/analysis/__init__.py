"""Analysis and failure boundary modules for Model Autopsy."""

from model_autopsy.analysis.failure_boundary import (
    MANDATED_BOUNDARY_CAPTION,
    MANDATED_SENSITIVITY_CAVEAT,
    FailureBoundaryResult,
    compute_feature_vulnerabilities,
    detect_failure_boundary,
)

__all__ = [
    "FailureBoundaryResult",
    "detect_failure_boundary",
    "compute_feature_vulnerabilities",
    "MANDATED_BOUNDARY_CAPTION",
    "MANDATED_SENSITIVITY_CAVEAT",
]
