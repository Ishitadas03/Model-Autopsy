"""Metric calculation, degradation tracking, and failure threshold evaluation."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support


@dataclass
class EvaluationMetrics:
    """Comprehensive evaluation metrics for a single evaluation step."""

    macro_f1: float
    accuracy: float
    per_class_f1: List[float]
    per_class_precision: List[float]
    per_class_recall: List[float]
    confusion_matrix: List[List[int]]
    absolute_degradation_pp: float
    relative_degradation_pct: float
    is_failed: bool
    rel_drop_exceeds_15_pct: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to serializable dictionary."""
        return asdict(self)


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    baseline_macro_f1: Optional[float] = None,
    failure_threshold: float = 0.80,
    n_classes: int = 3,
) -> EvaluationMetrics:
    """Compute primary, secondary, and degradation metrics for predictions.

    Definitions:
        - Primary Metric: Macro-Averaged F1-Score
        - Secondary Metric: Classification Accuracy
        - Confusion Matrix: C[k, l] records count of true class k predicted as l
        - Absolute Degradation (pp):
            absolute_degradation_pp = (baseline_macro_f1 - current_macro_f1) * 100.0
        - Relative Degradation (%):
            relative_degradation_pct = ((baseline_macro_f1 - current_macro_f1) / baseline_macro_f1) * 100.0
        - Primary Failure Rule:
            is_failed = current_macro_f1 < failure_threshold (Strict < comparison)
        - Diagnostic Flag:
            rel_drop_exceeds_15_pct = relative_degradation_pct > 15.0

    Note on Polarity:
        A positive degradation indicates performance loss (decay).
        A negative degradation indicates that the model performed slightly better
        under this specific perturbation instance than at baseline.

    Args:
        y_true: Ground truth integer class labels (n_samples,).
        y_pred: Predicted integer class labels (n_samples,).
        baseline_macro_f1: Macro-F1 achieved on uncorrupted baseline (s=0.00).
            If None, current_macro_f1 is treated as the baseline.
        failure_threshold: Fixed reliability threshold (default 0.80).
        n_classes: Total number of categorical classes (default 3).

    Returns:
        EvaluationMetrics instance.
    """
    if y_true.shape != y_pred.shape:
        raise ValueError(
            f"Shape mismatch: y_true shape {y_true.shape} != y_pred shape {y_pred.shape}"
        )
    if len(y_true) == 0:
        raise ValueError("Cannot calculate metrics on an empty array")

    # Primary metric
    raw_macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    macro_f1 = round(raw_macro_f1, 4)

    # Secondary metrics
    accuracy = round(float(accuracy_score(y_true, y_pred)), 4)

    # Per-class precision, recall, F1
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=list(range(n_classes)),
        zero_division=0,
    )

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=list(range(n_classes)))

    # Degradation metrics calculation
    ref_baseline = macro_f1 if baseline_macro_f1 is None else baseline_macro_f1

    # Absolute degradation in percentage points (pp) and relative degradation (%)
    if abs(ref_baseline - macro_f1) < 1e-9:
        absolute_degradation_pp = 0.0
        relative_degradation_pct = 0.0
    else:
        absolute_degradation_pp = round((ref_baseline - macro_f1) * 100.0, 4)
        if abs(ref_baseline) < 1e-12:
            relative_degradation_pct = 0.0
        else:
            relative_degradation_pct = round(((ref_baseline - macro_f1) / ref_baseline) * 100.0, 4)

    # Strict failure evaluation: Macro-F1 < failure_threshold
    # Strict less-than is required by scientific protocol
    is_failed = bool(macro_f1 < failure_threshold)

    # Separate diagnostic flag (NOT combined with primary failure rule)
    rel_drop_exceeds_15_pct = bool(relative_degradation_pct > 15.0)

    return EvaluationMetrics(
        macro_f1=macro_f1,
        accuracy=accuracy,
        per_class_f1=[round(float(v), 4) for v in f1],
        per_class_precision=[round(float(v), 4) for v in precision],
        per_class_recall=[round(float(v), 4) for v in recall],
        confusion_matrix=cm.tolist(),
        absolute_degradation_pp=absolute_degradation_pp,
        relative_degradation_pct=relative_degradation_pct,
        is_failed=is_failed,
        rel_drop_exceeds_15_pct=rel_drop_exceeds_15_pct,
    )
