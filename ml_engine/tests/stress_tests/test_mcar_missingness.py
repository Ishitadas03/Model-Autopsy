"""Unit tests for Missing Completely at Random (MCAR) feature perturbation operator."""

import numpy as np
import pytest

from model_autopsy.stress_tests.missingness.mcar import apply_feature_missingness_mcar


@pytest.fixture
def sample_features():
    rng = np.random.default_rng(1234)
    return rng.normal(loc=5.0, scale=1.5, size=(50, 4))


@pytest.fixture
def sample_train_mean():
    return np.array([5.1, 3.2, 4.4, 1.3], dtype=np.float64)


def test_severity_zero_exact_identity(sample_features, sample_train_mean):
    """Severity 0.0 must return an exact numerical copy without modifications."""
    res = apply_feature_missingness_mcar(
        X=sample_features,
        train_mean=sample_train_mean,
        severity=0.0,
        seed=42,
    )
    np.testing.assert_array_equal(res.X_corrupted, sample_features)
    assert res.metadata["is_control_baseline"] is True
    assert res.metadata["missing_cells_count"] == 0
    assert np.all(res.noise_matrix == 0.0)


def test_input_array_immutability(sample_features, sample_train_mean):
    """The original input feature matrix must remain unmodified."""
    original_copy = sample_features.copy()
    _ = apply_feature_missingness_mcar(
        X=sample_features,
        train_mean=sample_train_mean,
        severity=0.25,
        seed=42,
    )
    np.testing.assert_array_equal(sample_features, original_copy)


def test_output_array_read_only(sample_features, sample_train_mean):
    """Output matrices must be marked read-only."""
    res = apply_feature_missingness_mcar(
        X=sample_features,
        train_mean=sample_train_mean,
        severity=0.20,
        seed=42,
    )
    with pytest.raises(ValueError):
        res.X_corrupted[0, 0] = 999.0
    with pytest.raises(ValueError):
        res.noise_matrix[0, 0] = 999.0


def test_imputation_values_match_training_mean(sample_features, sample_train_mean):
    """Masked entries must be imputed with exact training mean for feature j."""
    res = apply_feature_missingness_mcar(
        X=sample_features,
        train_mean=sample_train_mean,
        severity=0.30,
        seed=42,
    )
    mask = res.noise_matrix.astype(bool)
    assert np.sum(mask) > 0, "Expected at least one masked cell at severity 0.30"

    for j in range(sample_features.shape[1]):
        col_mask = mask[:, j]
        if np.any(col_mask):
            np.testing.assert_allclose(
                res.X_corrupted[col_mask, j],
                sample_train_mean[j],
                err_msg=f"Feature {j} imputed value does not match train_mean",
            )


def test_deterministic_reproducibility(sample_features, sample_train_mean):
    """Same seed must produce bitwise identical missingness masks and values."""
    res1 = apply_feature_missingness_mcar(sample_features, sample_train_mean, severity=0.20, seed=777)
    res2 = apply_feature_missingness_mcar(sample_features, sample_train_mean, severity=0.20, seed=777)
    np.testing.assert_array_equal(res1.X_corrupted, res2.X_corrupted)
    np.testing.assert_array_equal(res1.noise_matrix, res2.noise_matrix)


def test_different_seeds_produce_different_masks(sample_features, sample_train_mean):
    """Distinct seeds must produce different missingness masks."""
    res1 = apply_feature_missingness_mcar(sample_features, sample_train_mean, severity=0.20, seed=1)
    res2 = apply_feature_missingness_mcar(sample_features, sample_train_mean, severity=0.20, seed=2)
    assert not np.array_equal(res1.noise_matrix, res2.noise_matrix)


def test_invalid_parameters_rejected(sample_features, sample_train_mean):
    """Negative severity or severity > 1.0 or mismatched shapes must raise ValueError."""
    with pytest.raises(ValueError, match="Severity"):
        apply_feature_missingness_mcar(sample_features, sample_train_mean, severity=-0.05)
    with pytest.raises(ValueError, match="Severity"):
        apply_feature_missingness_mcar(sample_features, sample_train_mean, severity=1.05)

    with pytest.raises(ValueError, match="Dimension mismatch"):
        apply_feature_missingness_mcar(sample_features, sample_train_mean[:2], severity=0.1)

    bad_features = sample_features.copy()
    bad_features[0, 0] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        apply_feature_missingness_mcar(bad_features, sample_train_mean, severity=0.1)
