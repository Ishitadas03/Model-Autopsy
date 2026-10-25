"""Unit tests for sample-level failure pattern analysis services (E004)."""

import numpy as np
import pytest

from model_autopsy.analysis.failure_patterns import (
    apply_benjamini_hochberg,
    calculate_class_vulnerabilities,
    calculate_error_persistence,
    calculate_exact_binomial_ci,
    calculate_inter_model_concordance,
    calculate_jaccard_similarity,
    calculate_mahalanobis_margins,
    calculate_sample_errors,
    calculate_seed_stability,
)


def test_calculate_sample_errors():
    y_true = np.array([0, 1, 2, 1, 0])
    y_pred = np.array([0, 2, 2, 1, 1])

    errors = calculate_sample_errors(y_true, y_pred)
    assert np.array_equal(errors, np.array([False, True, False, False, True]))


def test_calculate_sample_errors_mismatch_raises():
    with pytest.raises(ValueError):
        calculate_sample_errors(np.array([0, 1]), np.array([0]))


def test_clopper_pearson_bounds():
    # 0 out of 30
    low, high = calculate_exact_binomial_ci(0, 30)
    assert low == 0.0
    assert 0.0 < high < 0.20

    # 30 out of 30
    low, high = calculate_exact_binomial_ci(30, 30)
    assert 0.80 < low < 1.0
    assert high == 1.0

    # 10 out of 20
    low, high = calculate_exact_binomial_ci(10, 20)
    assert 0.25 < low < 0.50
    assert 0.50 < high < 0.75

    with pytest.raises(ValueError):
        calculate_exact_binomial_ci(-1, 30)
    with pytest.raises(ValueError):
        calculate_exact_binomial_ci(35, 30)


def test_calculate_error_persistence_edge_cases():
    severities = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
    y_true = np.array([0, 1, 2, 0])

    # Sample 0: Never fails
    # Sample 1: Fails at 0.10 and stays failed at all higher severities (perfect persistence = 1.0)
    # Sample 2: Fails at 0.10, correct at 0.15, fails at 0.20, 0.25, 0.30 (EPR = 4/5 = 0.8, POC = 3)
    # Sample 3: Fails only at maximum severity 0.30 (EPR = 1/1 = 1.0, POC = 1)
    preds = {
        0.0: np.array([0, 1, 2, 0]),
        0.05: np.array([0, 1, 2, 0]),
        0.10: np.array([0, 2, 1, 0]),
        0.15: np.array([0, 2, 2, 0]),
        0.20: np.array([0, 2, 1, 0]),
        0.25: np.array([0, 2, 1, 0]),
        0.30: np.array([0, 2, 1, 1]),
    }

    res = calculate_error_persistence(preds, y_true, severities)

    # Sample 0: Never fails
    rec0 = res["sample_records"][0]
    assert rec0["first_error_severity"] is None
    assert rec0["is_ever_failed"] is False
    assert rec0["error_persistence_ratio"] is None
    assert rec0["prediction_oscillation_count"] == 0

    # Sample 1: Absorbing failure at 0.10
    rec1 = res["sample_records"][1]
    assert rec1["first_error_severity"] == 0.10
    assert rec1["is_ever_failed"] is True
    assert rec1["error_persistence_ratio"] == 1.0
    assert rec1["prediction_oscillation_count"] == 1  # 1 -> 2 transition

    # Sample 2: Oscillating failure
    rec2 = res["sample_records"][2]
    assert rec2["first_error_severity"] == 0.10
    assert rec2["error_persistence_ratio"] == 0.8  # 4 errors out of 5 steps
    assert rec2["prediction_oscillation_count"] == 3  # 2->1 at 0.10, 1->2 at 0.15, 2->1 at 0.20

    # Sample 3: Fails only at max severity 0.30
    rec3 = res["sample_records"][3]
    assert rec3["first_error_severity"] == 0.30
    assert rec3["error_persistence_ratio"] == 1.0
    assert rec3["prediction_oscillation_count"] == 1

    # Aggregates
    assert res["n_total_samples"] == 4
    assert res["n_failed_samples"] == 3
    assert res["n_resilient_samples"] == 1
    # valid EPRs are [1.0, 0.8, 1.0] -> mean = 2.8 / 3 = 0.9333
    assert pytest.approx(res["mean_error_persistence_ratio"], 0.001) == 0.9333
    assert res["perfect_persistence_count"] == 2


def test_jaccard_similarity_edge_cases():
    # Identical sets
    assert calculate_jaccard_similarity({1, 2}, {1, 2}) == 1.0

    # Both empty sets (zero errors)
    assert calculate_jaccard_similarity(set(), set()) == 1.0

    # One empty, one non-empty
    assert calculate_jaccard_similarity(set(), {1}) == 0.0

    # Disjoint sets
    assert calculate_jaccard_similarity({1, 2}, {3, 4}) == 0.0

    # Partial overlap: {1, 2, 3} and {2, 3, 4} -> intersection=2, union=4 -> 0.5
    assert calculate_jaccard_similarity({1, 2, 3}, {2, 3, 4}) == 0.5


def test_calculate_inter_model_concordance():
    y_true = np.array([0, 1, 2, 0, 1])

    # RF fails on index 1, 2
    # LR fails on index 1, 3
    # GB fails on index 1, 2, 4
    preds = {
        "random_forest": np.array([0, 2, 1, 0, 1]),
        "logistic_regression": np.array([0, 2, 2, 1, 1]),
        "gradient_boosting": np.array([0, 2, 1, 0, 2]),
    }

    res = calculate_inter_model_concordance(preds, y_true)

    assert res["error_set_sizes"]["random_forest"] == 2
    assert res["error_set_sizes"]["logistic_regression"] == 2
    assert res["error_set_sizes"]["gradient_boosting"] == 3

    # Consensus failure: index 1 (all fail)
    assert res["consensus_error_indices"] == [1]

    # Unique failures:
    # RF errors: {1, 2}; others fail on 1 and 2, so RF has 0 unique
    assert res["unique_error_counts"]["random_forest"] == 0
    # LR errors: {1, 3}; 3 is only failed by LR
    assert res["unique_error_indices"]["logistic_regression"] == [3]
    # GB errors: {1, 2, 4}; 4 is only failed by GB
    assert res["unique_error_indices"]["gradient_boosting"] == [4]


def test_calculate_class_vulnerabilities():
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 0, 2, 1, 1, 2])  # 1 versicolor->virginica, 1 virginica->versicolor
    target_names = ["setosa", "versicolor", "virginica"]

    res = calculate_class_vulnerabilities(y_pred, y_true, target_names)

    assert res["per_class"]["setosa"]["error_count"] == 0
    assert res["per_class"]["setosa"]["error_rate"] == 0.0
    assert res["per_class"]["versicolor"]["error_count"] == 1
    assert res["per_class"]["versicolor"]["error_rate"] == 0.5
    assert res["per_class"]["virginica"]["error_count"] == 1
    assert res["per_class"]["virginica"]["error_rate"] == 0.5

    assert res["directed_confusions"]["versicolor_to_virginica"] == 1
    assert res["directed_confusions"]["virginica_to_versicolor"] == 1
    assert res["directed_confusions"]["setosa_to_versicolor"] == 0


def test_calculate_mahalanobis_margins():
    # Simple 2D separable data
    X_train = np.array([
        [0.0, 0.0], [0.1, 0.1], [0.2, -0.1],
        [5.0, 5.0], [5.1, 4.9], [4.9, 5.2]
    ])
    y_train = np.array([0, 0, 0, 1, 1, 1])

    X_test = np.array([
        [0.05, 0.05],  # Very close to class 0 centroid (large margin)
        [2.45, 2.45]   # Near boundary between class 0 and 1 (small margin)
    ])
    y_test = np.array([0, 0])

    early_failures = {1}
    resilient = {0}

    res = calculate_mahalanobis_margins(
        X_train, y_train, X_test, y_test, early_failures, resilient
    )

    margins = res["sample_margins"]
    assert margins[0]["opposing_class_margin"] > margins[1]["opposing_class_margin"]
    assert res["early_failing_group"]["n_samples"] == 1
    assert res["resilient_group"]["n_samples"] == 1
    assert res["hypothesis_test"]["u_statistic"] is not None


def test_calculate_seed_stability():
    y_true = np.array([0, 1, 2])
    # 5 seeds
    # sample 0: correct in all 5 seeds -> resilient
    # sample 1: wrong in all 5 seeds -> core_hard
    # sample 2: wrong in 2 of 5 seeds -> seed_vulnerable
    preds_across_seeds = [
        np.array([0, 2, 1]),
        np.array([0, 2, 1]),
        np.array([0, 2, 2]),
        np.array([0, 2, 2]),
        np.array([0, 2, 2]),
    ]

    res = calculate_seed_stability(preds_across_seeds, y_true)

    assert res["sample_stabilities"][0]["category"] == "resilient"
    assert res["sample_stabilities"][0]["failure_frequency"] == 0.0

    assert res["sample_stabilities"][1]["category"] == "core_hard"
    assert res["sample_stabilities"][1]["failure_frequency"] == 1.0

    assert res["sample_stabilities"][2]["category"] == "seed_vulnerable"
    assert res["sample_stabilities"][2]["failure_frequency"] == 0.4

    assert res["category_counts"]["resilient"] == 1
    assert res["category_counts"]["core_hard"] == 1
    assert res["category_counts"]["seed_vulnerable"] == 1


def test_benjamini_hochberg_fdr():
    # 5 hypotheses
    p_values = [0.001, 0.01, 0.03, 0.04, 0.50]
    bh_results = apply_benjamini_hochberg(p_values, q=0.05)

    assert len(bh_results) == 5
    # First p-value (0.001) should be significant
    assert bh_results[0]["is_significant_fdr"] is True
    # Highest p-value (0.50) should not be significant
    assert bh_results[4]["is_significant_fdr"] is False
