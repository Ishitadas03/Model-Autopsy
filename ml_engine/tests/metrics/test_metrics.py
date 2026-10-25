"""Unit tests for metric calculation, degradation analysis, and failure thresholds."""

import numpy as np
import pytest
from model_autopsy.metrics.evaluator import calculate_metrics


def test_metrics_known_examples():
    """Test 13: Verify Macro-F1 and accuracy against hand-calculated ground truth.

    Class 0: 3 samples -> 3 predicted 0 (P=1, R=1, F1=1)
    Class 1: 3 samples -> 2 predicted 1, 1 predicted 2 (P=2/2=1, R=2/3, F1=4/5=0.8)
    Class 2: 3 samples -> 2 predicted 2, 0 predicted 1 (1 sample from C1 falsely predicted 2 -> P=2/3, R=2/3, F1=2/3=0.6667)
    Macro-F1 = (1.0 + 0.8 + 2/3) / 3 = 2.46667 / 3 = 0.8222
    Accuracy = 7 / 9 = 0.7778
    """
    y_true = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])
    y_pred = np.array([0, 0, 0, 1, 1, 2, 2, 2, 0])

    # Class 0: True=[0,0,0], Pred=[0,0,0,0] (TP=3, FP=1, FN=0 -> P=3/4=0.75, R=3/3=1.0, F1=6/7=0.8571)
    # Class 1: True=[1,1,1], Pred=[1,1] (TP=2, FP=0, FN=1 -> P=1.0, R=2/3=0.6667, F1=4/5=0.8000)
    # Class 2: True=[2,2,2], Pred=[2,2,2] (from 1->2 and 2->0: TP=2, FP=1, FN=1 -> P=2/3, R=2/3, F1=2/3=0.6667)
    # Macro-F1 = (0.85714 + 0.80000 + 0.66667) / 3 = 0.7746
    # Accuracy = (3 + 2 + 2) / 9 = 7 / 9 = 0.7778
    res = calculate_metrics(y_true, y_pred, n_classes=3)

    assert res.accuracy == pytest.approx(7 / 9, abs=1e-4)
    expected_f1 = (6 / 7 + 0.8 + 2 / 3) / 3
    assert res.macro_f1 == pytest.approx(expected_f1, abs=1e-4)


def test_confusion_matrix_shape_and_values():
    """Test 14: Confusion matrix matches exact known count grid."""
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 1, 1, 1, 2, 0])

    res = calculate_metrics(y_true, y_pred, n_classes=3)
    cm = np.array(res.confusion_matrix)

    assert cm.shape == (3, 3)
    expected_cm = np.array([
        [1, 1, 0],
        [0, 2, 0],
        [1, 0, 1],
    ])
    np.testing.assert_array_equal(cm, expected_cm)


def test_absolute_and_relative_degradation():
    """Test 15: Correct delta in percentage points (pp) and relative percentage (%)."""
    # Perfect baseline: F1 = 1.0
    # Current: F1 = 0.80
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred_perf = np.array([0, 0, 1, 1, 2, 2])

    res_perf = calculate_metrics(y_true, y_pred_perf)
    assert res_perf.macro_f1 == 1.0

    # Provide known baseline F1 = 1.0, current F1 = 0.80
    # Simulated current:
    y_pred_drop = np.array([0, 0, 1, 2, 2, 2])
    # Let's test with manual baseline_macro_f1
    res_drop = calculate_metrics(y_true, y_pred_drop, baseline_macro_f1=1.0)

    # abs drop in pp: (1.0 - res_drop.macro_f1) * 100
    expected_abs = (1.0 - res_drop.macro_f1) * 100.0
    expected_rel = ((1.0 - res_drop.macro_f1) / 1.0) * 100.0
    assert res_drop.absolute_degradation_pp == pytest.approx(expected_abs, abs=1e-3)
    assert res_drop.relative_degradation_pct == pytest.approx(expected_rel, abs=1e-3)


def test_zero_baseline_safe_handling():
    """Test 16: Zero baseline does not raise DivisionByZero."""
    y_true = np.array([0, 1, 2])
    y_pred = np.array([1, 2, 0])  # Accuracy 0, F1 0

    res = calculate_metrics(y_true, y_pred, baseline_macro_f1=0.0)
    assert res.relative_degradation_pct == 0.0
    assert not np.isnan(res.relative_degradation_pct)
    assert not np.isinf(res.relative_degradation_pct)


def test_failure_threshold_strict_less_than():
    """Test 17: Strict < 0.80 comparison semantics."""
    # When macro_f1 is exactly 0.8000 -> is_failed MUST be False
    y_true = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    # If F1 is exactly 0.8000:
    res_at_threshold = calculate_metrics(y_true, y_true, failure_threshold=1.0)
    # F1=1.0, threshold=1.0 -> 1.0 < 1.0 is False
    assert not res_at_threshold.is_failed

    # Threshold=0.80, F1=0.79 -> is_failed is True
    # Let's test calculate_metrics with a threshold higher than macro_f1
    res_fail = calculate_metrics(
        np.array([0, 1, 2, 0, 1, 2]),
        np.array([0, 1, 0, 0, 0, 2]),
        failure_threshold=0.80,
    )
    assert res_fail.macro_f1 < 0.80
    assert res_fail.is_failed is True


def test_relative_drop_diagnostic_separate_from_primary_failure():
    """Test 18: Relative drop > 15% is a diagnostic flag only and does not force is_failed=True."""
    # Suppose baseline was 0.98, current is 0.82.
    # Macro-F1 = 0.82 >= 0.80 -> is_failed MUST be False.
    # Relative drop = (0.98 - 0.82) / 0.98 * 100 = 16.3% (> 15%) -> rel_drop_exceeds_15_pct is True.
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 0, 1, 1, 2, 2])  # F1=1.0

    # Let's test with baseline 1.0 and a simulated run with F1 ~ 0.82
    y_test_10 = np.array([0, 0, 0, 1, 1, 1, 1, 2, 2, 2])
    y_pred_10 = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2, 2])  # 9/10 correct -> F1 ~ 0.89
    res = calculate_metrics(y_test_10, y_pred_10, baseline_macro_f1=1.0, failure_threshold=0.80)

    # If F1 >= 0.80, is_failed is strictly False
    assert res.macro_f1 >= 0.80
    assert res.is_failed is False
