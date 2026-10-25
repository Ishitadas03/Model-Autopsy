"""Unit tests for Iris dataset loading, schema validation, and stratified splitting."""

import numpy as np
import pytest
from model_autopsy.datasets.iris import compute_array_hash, load_and_validate_iris


def test_iris_loading_and_shape_validation():
    """Test 1: Verify Iris features, targets, and partition shapes."""
    bundle = load_and_validate_iris(split_seed=42)

    # Validate shapes
    assert bundle.X_train.shape == (120, 4)
    assert bundle.y_train.shape == (120,)
    assert bundle.X_test.shape == (30, 4)
    assert bundle.y_test.shape == (30,)
    assert bundle.train_std.shape == (4,)

    # Validate feature names and targets
    assert len(bundle.feature_names) == 4
    assert len(bundle.target_names) == 3
    assert bundle.target_names == ["setosa", "versicolor", "virginica"]

    # Finiteness
    assert np.all(np.isfinite(bundle.X_train))
    assert np.all(np.isfinite(bundle.X_test))
    assert np.all(bundle.train_std > 0)


def test_stratified_split_reproducibility():
    """Test 2: Stratified split produces identical partitions for the same seed."""
    bundle_a = load_and_validate_iris(split_seed=42)
    bundle_b = load_and_validate_iris(split_seed=42)

    np.testing.assert_array_equal(bundle_a.train_indices, bundle_b.train_indices)
    np.testing.assert_array_equal(bundle_a.test_indices, bundle_b.test_indices)
    np.testing.assert_array_equal(bundle_a.X_train, bundle_b.X_train)
    np.testing.assert_array_equal(bundle_a.X_test, bundle_b.X_test)
    np.testing.assert_array_equal(bundle_a.train_std, bundle_b.train_std)
    assert bundle_a.dataset_hash == bundle_b.dataset_hash


def test_no_train_test_overlap():
    """Test 3: Zero sample overlap between training and testing indices."""
    bundle = load_and_validate_iris(split_seed=42)

    train_set = set(bundle.train_indices.tolist())
    test_set = set(bundle.test_indices.tolist())

    assert len(train_set) == 120
    assert len(test_set) == 30
    assert len(train_set.intersection(test_set)) == 0


def test_training_dispersion_isolation():
    """Verify training standard deviation is computed strictly on train partition with ddof=1."""
    bundle = load_and_validate_iris(split_seed=42)

    manual_std = np.std(bundle.X_train, axis=0, ddof=1)
    np.testing.assert_allclose(bundle.train_std, manual_std)

    # Confirm it does NOT equal full dataset or test standard deviation
    full_std = np.std(np.vstack([bundle.X_train, bundle.X_test]), axis=0, ddof=1)
    assert not np.allclose(bundle.train_std, full_std)


def test_array_immutability():
    """Verify bundle arrays cannot be inadvertently mutated in-place."""
    bundle = load_and_validate_iris(split_seed=42)

    with pytest.raises(ValueError):
        bundle.X_train[0, 0] = 999.0

    with pytest.raises(ValueError):
        bundle.X_test[0, 0] = 999.0
