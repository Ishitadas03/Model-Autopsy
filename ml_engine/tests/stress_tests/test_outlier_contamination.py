"""Unit tests for feature outlier contamination perturbation operator."""

import numpy as np
import pytest

from model_autopsy.stress_tests.outliers.impulsive import apply_feature_outliers


@pytest.fixture
def sample_features():
    rng = np.random.default_rng(5678)
    return rng.normal(loc=10.0, scale=2.0, size=(60, 4))


@pytest.fixture
def sample_train_stats():
    train_mean = np.array([10.1, 9.8, 10.3, 10.0], dtype=np.float64)
    train_std = np.array([2.1, 1.9, 2.0, 2.2], dtype=np.float64)
    return train_mean, train_std


def test_severity_zero_exact_identity(sample_features, sample_train_stats):
    """Severity 0.0 must return an exact numerical copy without modifications."""
    train_mean, train_std = sample_train_stats
    res = apply_feature_outliers(
        X=sample_features,
        train_mean=train_mean,
        train_std=train_std,
        severity=0.0,
        seed=42,
    )
    np.testing.assert_array_equal(res.X_corrupted, sample_features)
    assert res.metadata["is_control_baseline"] is True
    assert res.metadata["outlier_cells_count"] == 0
    assert np.all(res.noise_matrix == 0.0)


def test_input_array_immutability(sample_features, sample_train_stats):
    """The original input feature matrix must remain unmodified."""
    train_mean, train_std = sample_train_stats
    original_copy = sample_features.copy()
    _ = apply_feature_outliers(
        X=sample_features,
        train_mean=train_mean,
        train_std=train_std,
        severity=0.25,
        seed=42,
    )
    np.testing.assert_array_equal(sample_features, original_copy)


def test_output_array_read_only(sample_features, sample_train_stats):
    """Output matrices must be marked read-only."""
    train_mean, train_std = sample_train_stats
    res = apply_feature_outliers(
        X=sample_features,
        train_mean=train_mean,
        train_std=train_std,
        severity=0.20,
        seed=42,
    )
    with pytest.raises(ValueError):
        res.X_corrupted[0, 0] = 999.0
    with pytest.raises(ValueError):
        res.noise_matrix[0, 0] = 999.0


def test_outlier_values_formula(sample_features, sample_train_stats):
    """Contaminated entries must equal train_mean[j] +/- displacement * train_std[j]."""
    train_mean, train_std = sample_train_stats
    displacement = 5.0
    res = apply_feature_outliers(
        X=sample_features,
        train_mean=train_mean,
        train_std=train_std,
        severity=0.30,
        displacement_factor=displacement,
        seed=42,
    )
    mask = res.noise_matrix.astype(bool)
    assert np.sum(mask) > 0, "Expected at least one outlier at severity 0.30"

    for j in range(sample_features.shape[1]):
        col_mask = mask[:, j]
        if np.any(col_mask):
            values = res.X_corrupted[col_mask, j]
            expected_pos = train_mean[j] + displacement * train_std[j]
            expected_neg = train_mean[j] - displacement * train_std[j]
            # Each value must equal either expected_pos or expected_neg
            for val in values:
                assert np.isclose(val, expected_pos) or np.isclose(val, expected_neg)


def test_deterministic_reproducibility(sample_features, sample_train_stats):
    """Same seed must produce bitwise identical corrupted matrices."""
    train_mean, train_std = sample_train_stats
    res1 = apply_feature_outliers(sample_features, train_mean, train_std, severity=0.20, seed=888)
    res2 = apply_feature_outliers(sample_features, train_mean, train_std, severity=0.20, seed=888)
    np.testing.assert_array_equal(res1.X_corrupted, res2.X_corrupted)
    np.testing.assert_array_equal(res1.noise_matrix, res2.noise_matrix)


def test_invalid_parameters_rejected(sample_features, sample_train_stats):
    """Negative severity or non-positive displacement must raise ValueError."""
    train_mean, train_std = sample_train_stats
    with pytest.raises(ValueError, match="Severity"):
        apply_feature_outliers(sample_features, train_mean, train_std, severity=-0.1)
    with pytest.raises(ValueError, match="Severity"):
        apply_feature_outliers(sample_features, train_mean, train_std, severity=1.1)
    with pytest.raises(ValueError, match="displacement_factor"):
        apply_feature_outliers(sample_features, train_mean, train_std, severity=0.1, displacement_factor=0.0)
