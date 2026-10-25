"""Unit tests for Random Forest model adapter."""

import numpy as np
import pytest
from model_autopsy.models.sklearn_rf import RandomForestAdapter, RandomForestConfig


def test_random_forest_configuration_and_fitting():
    """Test 4: Verify default configuration, fitting, and prediction."""
    config = RandomForestConfig(
        n_estimators=100,
        max_depth=None,
        criterion="gini",
        min_samples_split=2,
        min_samples_leaf=1,
        bootstrap=True,
        random_state=42,
    )
    adapter = RandomForestAdapter(config=config)

    assert not adapter.is_fitted
    with pytest.raises(RuntimeError):
        adapter.predict(np.zeros((5, 4)))

    # Synthetic 3-class data
    X = np.array([
        [1.0, 2.0, 3.0, 4.0],
        [1.1, 2.1, 3.1, 4.1],
        [5.0, 6.0, 7.0, 8.0],
        [5.1, 6.1, 7.1, 8.1],
        [9.0, 8.0, 7.0, 6.0],
        [9.1, 8.1, 7.1, 6.1],
    ])
    y = np.array([0, 0, 1, 1, 2, 2])

    adapter.fit(X, y)
    assert adapter.is_fitted

    preds = adapter.predict(X)
    assert preds.shape == (6,)
    assert set(preds).issubset({0, 1, 2})

    probs = adapter.predict_proba(X)
    assert probs.shape == (6, 3)
    np.testing.assert_allclose(np.sum(probs, axis=1), 1.0)

    params = adapter.get_params()
    assert params["adapter"] == "RandomForestAdapter"
    assert params["hyperparameters"]["n_estimators"] == 100
    assert params["hyperparameters"]["random_state"] == 42
    assert params["is_fitted"] is True
