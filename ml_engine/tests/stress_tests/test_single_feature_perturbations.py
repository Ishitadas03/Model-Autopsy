"""Unit tests for coordinate-isolated single feature perturbation operators (RQ3/E005)."""

import numpy as np
import pytest

from model_autopsy.stress_tests.feature_corruption.single_feature import (
    apply_single_feature_gaussian_noise,
    apply_single_feature_missingness,
    apply_single_feature_outliers,
)


@pytest.fixture
def sample_feature_matrix() -> np.ndarray:
    """Create a fixed 2D feature matrix (30 samples, 4 features)."""
    rng = np.random.default_rng(12345)
    return rng.uniform(low=1.0, high=10.0, size=(30, 4))


@pytest.fixture
def sample_train_stats() -> tuple[np.ndarray, np.ndarray]:
    """Create sample train_mean and train_std vectors for 4 features."""
    train_mean = np.array([5.5, 3.2, 4.8, 1.5], dtype=np.float64)
    train_std = np.array([0.8, 0.4, 1.2, 0.5], dtype=np.float64)
    return train_mean, train_std


def test_single_feature_gaussian_noise_severity_zero_identity(
    sample_feature_matrix: np.ndarray, sample_train_stats: tuple[np.ndarray, np.ndarray]
):
    """Test 1: Severity 0.00 returns bitwise identical copy for Gaussian noise."""
    _, train_std = sample_train_stats
    result = apply_single_feature_gaussian_noise(
        sample_feature_matrix, train_std=train_std, feature_index=2, severity=0.0, seed=42
    )
    assert np.array_equal(result.X_corrupted, sample_feature_matrix)
    assert result.metadata["is_control_baseline"] is True
    assert np.all(result.noise_matrix == 0.0)


def test_single_feature_missingness_severity_zero_identity(
    sample_feature_matrix: np.ndarray, sample_train_stats: tuple[np.ndarray, np.ndarray]
):
    """Test 2: Severity 0.00 returns bitwise identical copy for missingness."""
    train_mean, _ = sample_train_stats
    result = apply_single_feature_missingness(
        sample_feature_matrix, train_mean=train_mean, feature_index=1, severity=0.0, seed=42
    )
    assert np.array_equal(result.X_corrupted, sample_feature_matrix)
    assert result.metadata["is_control_baseline"] is True
    assert np.all(result.noise_matrix == 0.0)


def test_single_feature_outliers_severity_zero_identity(
    sample_feature_matrix: np.ndarray, sample_train_stats: tuple[np.ndarray, np.ndarray]
):
    """Test 3: Severity 0.00 returns bitwise identical copy for outliers."""
    train_mean, train_std = sample_train_stats
    result = apply_single_feature_outliers(
        sample_feature_matrix, train_mean=train_mean, train_std=train_std, feature_index=3, severity=0.0, seed=42
    )
    assert np.array_equal(result.X_corrupted, sample_feature_matrix)
    assert result.metadata["is_control_baseline"] is True
    assert np.all(result.noise_matrix == 0.0)


def test_single_feature_isolation_gaussian_noise(
    sample_feature_matrix: np.ndarray, sample_train_stats: tuple[np.ndarray, np.ndarray]
):
    """Test 4: Only the targeted feature is perturbed; all other columns remain bitwise untouched."""
    _, train_std = sample_train_stats
    target_idx = 1
    result = apply_single_feature_gaussian_noise(
        sample_feature_matrix, train_std=train_std, feature_index=target_idx, severity=0.20, seed=42
    )

    # Targeted column must be perturbed
    assert not np.array_equal(result.X_corrupted[:, target_idx], sample_feature_matrix[:, target_idx])
    # Non-targeted columns must remain 100% bitwise identical
    for j in range(4):
        if j != target_idx:
            assert np.array_equal(result.X_corrupted[:, j], sample_feature_matrix[:, j])
            assert np.all(result.noise_matrix[:, j] == 0.0)


def test_single_feature_isolation_missingness(
    sample_feature_matrix: np.ndarray, sample_train_stats: tuple[np.ndarray, np.ndarray]
):
    """Test 5: Missingness operator perturbs only target column with training mean."""
    train_mean, _ = sample_train_stats
    target_idx = 2
    result = apply_single_feature_missingness(
        sample_feature_matrix, train_mean=train_mean, feature_index=target_idx, severity=0.30, seed=42
    )

    # Targeted column contains imputed values
    assert not np.array_equal(result.X_corrupted[:, target_idx], sample_feature_matrix[:, target_idx])
    # Check that any altered cells match train_mean[target_idx]
    altered = result.X_corrupted[:, target_idx] != sample_feature_matrix[:, target_idx]
    if np.any(altered):
        assert np.allclose(result.X_corrupted[altered, target_idx], train_mean[target_idx])

    # Non-targeted columns untouched
    for j in range(4):
        if j != target_idx:
            assert np.array_equal(result.X_corrupted[:, j], sample_feature_matrix[:, j])


def test_single_feature_isolation_outliers(
    sample_feature_matrix: np.ndarray, sample_train_stats: tuple[np.ndarray, np.ndarray]
):
    """Test 6: Outlier operator perturbs only target column with 5*std displacement."""
    train_mean, train_std = sample_train_stats
    target_idx = 0
    result = apply_single_feature_outliers(
        sample_feature_matrix, train_mean=train_mean, train_std=train_std, feature_index=target_idx,
        severity=0.30, displacement_factor=5.0, seed=42
    )

    # Targeted column perturbed
    assert not np.array_equal(result.X_corrupted[:, target_idx], sample_feature_matrix[:, target_idx])
    # Check displacement formula on altered cells
    altered = result.X_corrupted[:, target_idx] != sample_feature_matrix[:, target_idx]
    if np.any(altered):
        displaced_vals = result.X_corrupted[altered, target_idx]
        expected_pos = train_mean[target_idx] + 5.0 * train_std[target_idx]
        expected_neg = train_mean[target_idx] - 5.0 * train_std[target_idx]
        matches = np.isclose(displaced_vals, expected_pos) | np.isclose(displaced_vals, expected_neg)
        assert np.all(matches)

    # Non-targeted columns untouched
    for j in range(4):
        if j != target_idx:
            assert np.array_equal(result.X_corrupted[:, j], sample_feature_matrix[:, j])


def test_input_immutability_and_output_read_only(
    sample_feature_matrix: np.ndarray, sample_train_stats: tuple[np.ndarray, np.ndarray]
):
    """Test 7: Input array is not mutated and output array is marked read-only."""
    train_mean, train_std = sample_train_stats
    X_original = sample_feature_matrix.copy()

    result = apply_single_feature_gaussian_noise(
        sample_feature_matrix, train_std=train_std, feature_index=1, severity=0.15, seed=42
    )
    # Original input matrix remains unmodified
    assert np.array_equal(sample_feature_matrix, X_original)
    # Output arrays are read-only
    assert result.X_corrupted.flags.writeable is False
    assert result.noise_matrix.flags.writeable is False


def test_deterministic_reproducibility_across_operators(
    sample_feature_matrix: np.ndarray, sample_train_stats: tuple[np.ndarray, np.ndarray]
):
    """Test 8: Identical seed produces bitwise identical corrupted matrices."""
    train_mean, train_std = sample_train_stats

    # Gaussian
    res_g1 = apply_single_feature_gaussian_noise(sample_feature_matrix, train_std=train_std, feature_index=0, severity=0.25, seed=123)
    res_g2 = apply_single_feature_gaussian_noise(sample_feature_matrix, train_std=train_std, feature_index=0, severity=0.25, seed=123)
    assert np.array_equal(res_g1.X_corrupted, res_g2.X_corrupted)

    # Missingness
    res_m1 = apply_single_feature_missingness(sample_feature_matrix, train_mean=train_mean, feature_index=2, severity=0.20, seed=456)
    res_m2 = apply_single_feature_missingness(sample_feature_matrix, train_mean=train_mean, feature_index=2, severity=0.20, seed=456)
    assert np.array_equal(res_m1.X_corrupted, res_m2.X_corrupted)

    # Outliers
    res_o1 = apply_single_feature_outliers(sample_feature_matrix, train_mean=train_mean, train_std=train_std, feature_index=3, severity=0.15, seed=789)
    res_o2 = apply_single_feature_outliers(sample_feature_matrix, train_mean=train_mean, train_std=train_std, feature_index=3, severity=0.15, seed=789)
    assert np.array_equal(res_o1.X_corrupted, res_o2.X_corrupted)


def test_invalid_parameters_rejected(
    sample_feature_matrix: np.ndarray, sample_train_stats: tuple[np.ndarray, np.ndarray]
):
    """Test 9: Invalid feature indices and severities raise ValueError."""
    train_mean, train_std = sample_train_stats

    # Negative severity
    with pytest.raises(ValueError):
        apply_single_feature_gaussian_noise(sample_feature_matrix, train_std=train_std, feature_index=0, severity=-0.1)

    # Out of bounds feature index
    with pytest.raises(ValueError):
        apply_single_feature_gaussian_noise(sample_feature_matrix, train_std=train_std, feature_index=4, severity=0.1)
    with pytest.raises(ValueError):
        apply_single_feature_gaussian_noise(sample_feature_matrix, train_std=train_std, feature_index=-1, severity=0.1)

    # Mismatched train_std length
    with pytest.raises(ValueError):
        apply_single_feature_gaussian_noise(sample_feature_matrix, train_std=np.array([1.0, 2.0]), feature_index=0, severity=0.1)
