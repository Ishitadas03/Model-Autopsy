"""Unit tests for additive Gaussian noise stress testing."""

import numpy as np
import pytest
from model_autopsy.stress_tests.noise.gaussian import apply_gaussian_noise


@pytest.fixture
def sample_data():
    X = np.array([
        [5.1, 3.5, 1.4, 0.2],
        [4.9, 3.0, 1.4, 0.2],
        [4.7, 3.2, 1.3, 0.2],
        [7.0, 3.2, 4.7, 1.4],
        [6.4, 3.2, 4.5, 1.5],
        [6.3, 3.3, 6.0, 2.5],
    ])
    train_std = np.array([0.828, 0.435, 1.765, 0.762])
    return X, train_std


def test_gaussian_noise_output_shape(sample_data):
    """Test 5: Corrupted matrix has identical dimensions as input."""
    X, train_std = sample_data
    res = apply_gaussian_noise(X, train_std, severity=0.10, seed=42)

    assert res.X_corrupted.shape == X.shape
    assert res.noise_matrix.shape == X.shape


def test_correct_noise_scaling(sample_data):
    """Test 6: Verify variance of generated noise matches (severity * train_std)^2 empirically."""
    X, train_std = sample_data
    # Use large sample to verify empirical standard deviation
    n_large = 100_000
    X_large = np.zeros((n_large, len(train_std)))
    severity = 0.20
    res = apply_gaussian_noise(X_large, train_std, severity=severity, seed=42)

    expected_stds = severity * train_std
    empirical_stds = np.std(res.noise_matrix, axis=0)

    # Within 3% tolerance for 100,000 draws
    np.testing.assert_allclose(empirical_stds, expected_stds, rtol=0.03)


def test_severity_zero_exact_identity(sample_data):
    """Test 7: Severity 0.00 returns exactly unchanged values (bitwise identical)."""
    X, train_std = sample_data
    res = apply_gaussian_noise(X, train_std, severity=0.00, seed=42)

    # Bitwise exact equality
    np.testing.assert_array_equal(res.X_corrupted, X)
    assert np.all(res.noise_matrix == 0.0)
    assert res.metadata["is_control_baseline"] is True


def test_noise_reproducibility_same_seed(sample_data):
    """Test 8: Noise generation is bitwise identical for identical seed."""
    X, train_std = sample_data
    res_a = apply_gaussian_noise(X, train_std, severity=0.15, seed=42)
    res_b = apply_gaussian_noise(X, train_std, severity=0.15, seed=42)

    np.testing.assert_array_equal(res_a.X_corrupted, res_b.X_corrupted)
    np.testing.assert_array_equal(res_a.noise_matrix, res_b.noise_matrix)


def test_different_seeds_produce_different_noise(sample_data):
    """Test 9: Distinct seeds produce distinct perturbation values."""
    X, train_std = sample_data
    res_a = apply_gaussian_noise(X, train_std, severity=0.15, seed=42)
    res_b = apply_gaussian_noise(X, train_std, severity=0.15, seed=999)

    assert not np.array_equal(res_a.X_corrupted, res_b.X_corrupted)


def test_input_array_immutability(sample_data):
    """Test 10: Input feature matrix and train_std are not mutated in-place."""
    X, train_std = sample_data
    X_copy = X.copy()
    train_std_copy = train_std.copy()

    _ = apply_gaussian_noise(X, train_std, severity=0.25, seed=42)

    np.testing.assert_array_equal(X, X_copy)
    np.testing.assert_array_equal(train_std, train_std_copy)


def test_invalid_severity_rejected(sample_data):
    """Test 11: Negative severities are rejected with ValueError."""
    X, train_std = sample_data
    with pytest.raises(ValueError, match="Severity must be non-negative"):
        apply_gaussian_noise(X, train_std, severity=-0.05, seed=42)


def test_invalid_dimensions_rejected(sample_data):
    """Test 12: Incompatible feature dimensions between X and train_std are rejected."""
    X, train_std = sample_data
    wrong_std = np.array([1.0, 2.0])  # Only 2 features for 4-feature X

    with pytest.raises(ValueError, match="Dimension mismatch"):
        apply_gaussian_noise(X, wrong_std, severity=0.10, seed=42)

    # 1D X matrix rejected
    with pytest.raises(ValueError, match="X must be a 2D array"):
        apply_gaussian_noise(np.array([1.0, 2.0, 3.0, 4.0]), train_std, severity=0.10)
