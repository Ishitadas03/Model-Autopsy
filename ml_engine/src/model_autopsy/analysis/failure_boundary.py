"""Failure boundary characterization and empirical vulnerability analysis."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
import numpy as np


@dataclass
class FailureBoundaryResult:
    """Result of failure boundary evaluation across tested severity levels."""

    observed_boundary: Optional[float]
    is_boundary_observed: bool
    threshold: float
    tested_severities: List[float]
    boundary_caption: str
    summary_message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to serializable dictionary."""
        return asdict(self)


MANDATED_BOUNDARY_CAPTION = (
    "Observed failure boundary under the specified experimental configuration."
)

MANDATED_SENSITIVITY_CAVEAT = (
    "Empirical sensitivity — not a causal explanation."
)


def detect_failure_boundary(
    severity_records: List[Dict[str, Any]],
    failure_threshold: float = 0.80,
    metric_key: str = "macro_f1",
) -> FailureBoundaryResult:
    """Detect the empirical failure boundary s* from an ordered sequence of severity evaluations.

    Formal Definition:
        s* = min { s in S | Metric(s) < failure_threshold }

    Rules:
        - Strict less-than comparison: Metric(s) < failure_threshold
        - If all severities maintain Metric(s) >= failure_threshold, s* is unobserved (s* > max(S)).
        - Returns mandated caption verbatim.

    Args:
        severity_records: List of dictionaries, each containing at least 'severity' and metric_key.
        failure_threshold: Strict upper bound for failure (default 0.80).
        metric_key: Key for evaluating failure (default 'macro_f1').

    Returns:
        FailureBoundaryResult instance.
    """
    if not severity_records:
        raise ValueError("Cannot detect failure boundary from empty severity records")

    # Sort records ascending by severity
    sorted_records = sorted(severity_records, key=lambda r: float(r["severity"]))
    tested_severities = [float(r["severity"]) for r in sorted_records]

    observed_boundary: Optional[float] = None
    for record in sorted_records:
        sev = float(record["severity"])
        metric_val = float(record[metric_key])
        if metric_val < failure_threshold:
            observed_boundary = sev
            break

    if observed_boundary is not None:
        summary_message = (
            f"Observed failure boundary detected at s* = {observed_boundary:.2f} "
            f"({metric_key} = {record[metric_key]:.4f} < {failure_threshold:.2f})."
        )
        is_observed = True
    else:
        max_tested = max(tested_severities)
        summary_message = (
            f"Failure boundary not observed within tested severity range (s* > {max_tested:.2f}). "
            f"Model maintained {metric_key} >= {failure_threshold:.2f} across all tested levels."
        )
        is_observed = False

    return FailureBoundaryResult(
        observed_boundary=observed_boundary,
        is_boundary_observed=is_observed,
        threshold=failure_threshold,
        tested_severities=tested_severities,
        boundary_caption=MANDATED_BOUNDARY_CAPTION,
        summary_message=summary_message,
    )


def compute_feature_vulnerabilities(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    train_std: np.ndarray,
    feature_names: List[str],
    eval_severity: float = 0.20,
    baseline_macro_f1: float = 1.0,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """Compute empirical feature sensitivity by perturbing each feature independently.

    Mandated Caveat:
        'Empirical sensitivity — not a causal explanation.'

    Args:
        model: Fitted model adapter.
        X_test: Uncorrupted test feature matrix.
        y_test: Ground truth labels.
        train_std: Training feature standard deviations.
        feature_names: Names of input features.
        eval_severity: Severity level to evaluate feature sensitivity at (default 0.20).
        baseline_macro_f1: Uncorrupted baseline Macro-F1 score.
        seed: Seed for Gaussian PRNG.

    Returns:
        List of feature vulnerability rankings sorted by degradation drop descending.
    """
    from model_autopsy.metrics.evaluator import calculate_metrics
    from model_autopsy.stress_tests.noise.gaussian import apply_gaussian_noise

    vulnerabilities = []
    n_features = X_test.shape[1]

    for j in range(n_features):
        # Create single-feature perturbed matrix
        X_single = X_test.copy()
        single_train_std = train_std[j : j + 1]
        single_feature_matrix = X_test[:, j : j + 1]

        pert_res = apply_gaussian_noise(
            single_feature_matrix,
            train_std=single_train_std,
            severity=eval_severity,
            seed=seed + j,
        )
        X_single[:, j] = pert_res.X_corrupted[:, 0]

        preds = model.predict(X_single)
        metrics = calculate_metrics(y_test, preds, baseline_macro_f1=baseline_macro_f1)
        drop = round(baseline_macro_f1 - metrics.macro_f1, 4)

        vulnerabilities.append({
            "feature": feature_names[j],
            "feature_index": j,
            "drop": max(0.0, drop),
            "macro_f1_isolated": metrics.macro_f1,
            "accuracy_isolated": metrics.accuracy,
            "caveat": MANDATED_SENSITIVITY_CAVEAT,
        })

    # Sort descending by drop
    vulnerabilities.sort(key=lambda item: item["drop"], reverse=True)
    for rank_idx, item in enumerate(vulnerabilities, start=1):
        item["rank"] = rank_idx

    return vulnerabilities
