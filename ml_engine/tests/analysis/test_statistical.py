"""Unit tests for statistical aggregation, dispersion, SEM, and Student's t confidence intervals."""

import math
import numpy as np
import pytest
from scipy import stats

from model_autopsy.analysis.statistical import (
    aggregate_multi_seed_results,
    compute_sample_statistics,
)


def test_means_calculated_correctly():
    """Test 3: Sample mean arithmetic correctness."""
    values = [0.80, 0.85, 0.90, 0.95, 1.00]
    res = compute_sample_statistics(values)
    assert res.mean == pytest.approx(0.90, abs=1e-4)
    assert res.n == 5


def test_sample_std_uses_ddof_1():
    """Test 4: Sample standard deviation strictly uses ddof=1 (unbiased sample estimator).

    For values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]:
    mean = 5.0
    sum of squared deviations = 9 + 1 + 1 + 1 + 0 + 0 + 4 + 16 = 32
    Sample variance (ddof=1) = 32 / (8 - 1) = 32 / 7 = 4.5714 -> std = sqrt(4.5714) = 2.1381
    Population variance (ddof=0) = 32 / 8 = 4.0 -> std = 2.0
    """
    values = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    res = compute_sample_statistics(values)

    expected_sample_std = float(np.std(values, ddof=1))
    population_std = float(np.std(values, ddof=0))

    assert res.sample_std == pytest.approx(expected_sample_std, abs=1e-4)
    assert res.sample_std != pytest.approx(population_std, abs=1e-2)


def test_sem_calculation_correctness():
    """Test 5: Standard Error of the Mean is sample_std / sqrt(n)."""
    values = [0.88, 0.92, 0.90, 0.94, 0.86]
    res = compute_sample_statistics(values)

    expected_sem = res.sample_std / math.sqrt(len(values))
    assert res.sem == pytest.approx(expected_sem, abs=1e-4)


def test_student_t_confidence_interval_df():
    """Test 6: Student's t CI uses exact df = n - 1 (df = 4 for n = 5)."""
    values = [0.88, 0.92, 0.90, 0.94, 0.86]  # n = 5
    res = compute_sample_statistics(values, confidence=0.95)

    assert res.df == 4
    # For df=4, 95% two-sided t critical value is ~ 2.7764
    expected_t = float(stats.t.ppf(0.975, df=4))
    assert res.t_critical == pytest.approx(expected_t, abs=1e-3)
    assert res.t_critical == pytest.approx(2.7764, abs=1e-3)


def test_confidence_interval_contains_mean():
    """Test 7: Confidence interval bounds strictly contain the sample mean."""
    values = [0.82, 0.89, 0.91, 0.95, 0.88]
    res = compute_sample_statistics(values)

    assert res.ci_lower < res.mean
    assert res.ci_upper > res.mean
    assert res.ci_upper - res.mean == pytest.approx(res.mean - res.ci_lower, abs=1e-4)


def test_failure_proportions_calculated_correctly():
    """Test 8: Failure count and proportion across runs match threshold condition."""
    # 5 runs: 2 runs fail (< 0.80), 3 runs pass
    mock_runs = {
        42: {"severity_records": [{"severity": 0.10, "macro_f1": 0.85, "accuracy": 0.87, "absolute_degradation_pp": 5.0, "relative_degradation_pct": 5.5}]},
        123: {"severity_records": [{"severity": 0.10, "macro_f1": 0.78, "accuracy": 0.80, "absolute_degradation_pp": 12.0, "relative_degradation_pct": 13.3}]},  # FAIL
        456: {"severity_records": [{"severity": 0.10, "macro_f1": 0.91, "accuracy": 0.90, "absolute_degradation_pp": 0.0, "relative_degradation_pct": 0.0}]},
        789: {"severity_records": [{"severity": 0.10, "macro_f1": 0.76, "accuracy": 0.77, "absolute_degradation_pp": 14.0, "relative_degradation_pct": 15.5}]},  # FAIL
        1011: {"severity_records": [{"severity": 0.10, "macro_f1": 0.88, "accuracy": 0.90, "absolute_degradation_pp": 2.0, "relative_degradation_pct": 2.2}]},
    }

    res = aggregate_multi_seed_results(mock_runs, severities=[0.10], failure_threshold=0.80)
    agg = res.severity_aggregates[0]

    assert agg.failure_count == 2
    assert agg.failure_proportion == pytest.approx(0.40, abs=1e-4)
    # Mean Macro-F1 = (0.85 + 0.78 + 0.91 + 0.76 + 0.88) / 5 = 4.18 / 5 = 0.8360 >= 0.80
    assert not agg.is_mean_failed


def test_individual_boundaries_distinct_from_mean_boundaries():
    """Test 9: Methodological distinction between individual seed boundaries and mean failure boundary."""
    # At severity 0.15:
    # Seed 123 crosses (<0.80), but mean across all seeds remains >= 0.80
    mock_runs = {
        42: {
            "failure_boundary": {"observed_boundary": None},
            "severity_records": [
                {"severity": 0.15, "macro_f1": 0.85, "accuracy": 0.87, "absolute_degradation_pp": 5.0, "relative_degradation_pct": 5.5},
            ],
        },
        123: {
            "failure_boundary": {"observed_boundary": 0.15},
            "severity_records": [
                {"severity": 0.15, "macro_f1": 0.75, "accuracy": 0.77, "absolute_degradation_pp": 15.0, "relative_degradation_pct": 16.6},
            ],
        },
        456: {
            "failure_boundary": {"observed_boundary": None},
            "severity_records": [
                {"severity": 0.15, "macro_f1": 0.88, "accuracy": 0.90, "absolute_degradation_pp": 2.0, "relative_degradation_pct": 2.2},
            ],
        },
    }

    res = aggregate_multi_seed_results(mock_runs, severities=[0.15], failure_threshold=0.80)

    # Individual boundary occurred at 0.15
    assert res.earliest_individual_boundary == 0.15
    # Mean = (0.85 + 0.75 + 0.88) / 3 = 0.8267 >= 0.80 -> Mean boundary is unobserved (None)
    assert res.mean_observed_boundary is None


def test_failed_runs_reported_transparently():
    """Test 10: Run errors are preserved and transparently counted."""
    mock_runs = {
        42: {"severity_records": [{"severity": 0.00, "macro_f1": 0.90, "accuracy": 0.90, "absolute_degradation_pp": 0.0, "relative_degradation_pct": 0.0}]},
    }
    failed_details = [
        {"seed": 999, "error": "CUDA out of memory simulation", "error_type": "RuntimeError"}
    ]

    res = aggregate_multi_seed_results(
        mock_runs,
        severities=[0.00],
        failed_seeds=failed_details,
    )

    assert res.n_successful_seeds == 1
    assert res.n_failed_seeds == 1
    assert res.n_total_seeds == 2
    assert res.failed_seed_details[0]["seed"] == 999
