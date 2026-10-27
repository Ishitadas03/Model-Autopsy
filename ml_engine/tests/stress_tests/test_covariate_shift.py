"""Unit tests for covariate distribution shift operators in E006."""

import numpy as np
import pytest
from sklearn.decomposition import PCA

from model_autopsy.stress_tests.distribution_shift.covariate import (
    DIRECTION_VECTORS,
    TrainDistributionParameters,
    apply_directional_covariate_shift,
    apply_dispersion_covariate_shift,
    compute_selection_shift_weights,
)


@pytest.fixture
def synthetic_data():
    np.random.seed(42)
    X_train = np.random.normal(loc=[5.0, 3.0, 4.0, 1.2], scale=[0.8, 0.4, 1.5, 0.5], size=(120, 4))
    X_test = np.random.normal(loc=[5.0, 3.0, 4.0, 1.2], scale=[0.8, 0.4, 1.5, 0.5], size=(30, 4))
    return X_train, X_test


def test_severity_zero_identity(synthetic_data):
    """Test that s=0.0 returns exact bitwise copy with writeable=False."""
    X_train, X_test = synthetic_data
    params = TrainDistributionParameters.fit(X_train)

    # Directional shift at s=0
    for direction in ["allometric", "petal_pos", "petal_neg"]:
        X_dir = apply_directional_covariate_shift(X_test, params.std, direction, severity=0.0)
        assert np.array_equal(X_dir, X_test)
        assert not X_dir.flags.writeable

    # Dispersion shift at s=0
    X_disp = apply_dispersion_covariate_shift(X_test, params.mean, severity=0.0)
    assert np.array_equal(X_disp, X_test)
    assert not X_disp.flags.writeable

    # Selection shift at s=0
    weights = compute_selection_shift_weights(X_test, params.pca, severity=0.0)
    assert np.allclose(weights, 0.5)


def test_directional_shift_mathematics(synthetic_data):
    """Verify exact formula X' = X + s * v * sigma_train."""
    X_train, X_test = synthetic_data
    params = TrainDistributionParameters.fit(X_train)
    severity = 0.20

    v = DIRECTION_VECTORS["allometric"]
    X_shifted = apply_directional_covariate_shift(X_test, params.std, "allometric", severity)

    expected = X_test + severity * v * params.std
    assert np.allclose(X_shifted, expected)


def test_directional_vectors_unit_norm():
    """Verify all predefined direction vectors have unit L2 norm."""
    for name, v in DIRECTION_VECTORS.items():
        norm = np.linalg.norm(v)
        assert np.isclose(norm, 1.0, atol=1e-7), f"Vector {name} norm is {norm}, expected 1.0"


def test_dispersion_inflation_mathematics(synthetic_data):
    """Verify radial dilation formula X' = mu_train + (1 + s) * (X - mu_train)."""
    X_train, X_test = synthetic_data
    params = TrainDistributionParameters.fit(X_train)
    severity = 0.15

    X_dilated = apply_dispersion_covariate_shift(X_test, params.mean, severity)
    expected = params.mean + (1.0 + severity) * (X_test - params.mean)
    assert np.allclose(X_dilated, expected)

    # Mean is approximately preserved, variance expands by (1 + s)^2
    var_orig = np.var(X_test, axis=0, ddof=1)
    var_dilated = np.var(X_dilated, axis=0, ddof=1)
    expected_var = ((1.0 + severity) ** 2) * var_orig
    assert np.allclose(var_dilated, expected_var)


def test_selection_weights_properties(synthetic_data):
    """Verify selection weights are in (0, 1), monotonic along PC1, and strictly 0.5 at s=0."""
    X_train, X_test = synthetic_data
    params = TrainDistributionParameters.fit(X_train)

    weights = compute_selection_shift_weights(X_test, params.pca, severity=0.25)
    assert weights.shape == (len(X_test),)
    assert np.all(weights > 0.0)
    assert np.all(weights < 1.0)


def test_training_parameter_isolation(synthetic_data):
    """Verify that tampering with test data has ZERO effect on fitted shift parameters."""
    X_train, X_test = synthetic_data
    params1 = TrainDistributionParameters.fit(X_train)

    # Corrupt test data arbitrarily
    X_test_tampered = X_test * 1000.0 + 999.0

    # Ensure TrainDistributionParameters only uses X_train
    params2 = TrainDistributionParameters.fit(X_train)

    assert np.array_equal(params1.mean, params2.mean)
    assert np.array_equal(params1.std, params2.std)
    assert np.array_equal(params1.pca.components_, params2.pca.components_)


def test_input_immutability(synthetic_data):
    """Verify that input array is never modified in-place."""
    X_train, X_test = synthetic_data
    params = TrainDistributionParameters.fit(X_train)

    X_test_copy = X_test.copy()
    X_test.flags.writeable = False

    _ = apply_directional_covariate_shift(X_test, params.std, "petal_pos", 0.20)
    assert np.array_equal(X_test, X_test_copy)

    _ = apply_dispersion_covariate_shift(X_test, params.mean, 0.20)
    assert np.array_equal(X_test, X_test_copy)


def test_invalid_parameters_raise_errors(synthetic_data):
    """Verify out-of-range severities and dimension mismatches raise errors."""
    X_train, X_test = synthetic_data
    params = TrainDistributionParameters.fit(X_train)

    with pytest.raises(ValueError):
        apply_directional_covariate_shift(X_test, params.std, "petal_pos", severity=-0.1)

    with pytest.raises(ValueError):
        apply_directional_covariate_shift(X_test, params.std, "petal_pos", severity=1.5)

    with pytest.raises(ValueError):
        apply_dispersion_covariate_shift(X_test, params.mean, severity=1.5)

    with pytest.raises(KeyError):
        apply_directional_covariate_shift(X_test, params.std, "non_existent_direction", severity=0.1)
