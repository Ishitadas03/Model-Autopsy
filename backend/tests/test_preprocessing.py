"""Regression tests for train-only preprocessing and target validation."""
import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split

from app.services.preprocessing import prepare_holdout


def test_numeric_imputation_is_fitted_only_to_training_partition():
    df = pd.DataFrame({
        "income": [1.0, 2.0, 3.0, 1000.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0],
        "label": [0, 1] * 5,
    })
    raw_train, raw_test = train_test_split(
        df[["income"]], test_size=0.2, random_state=42, stratify=df["label"]
    )
    expected_median = float(raw_train["income"].median())
    train, test, y_train, y_test, classes, names = prepare_holdout(
        df, "label", "classification", 0.2, 42
    )
    assert names == ["income"]
    assert classes == ["0", "1"]
    assert np.isfinite(train).all() and np.isfinite(test).all()
    # Both known and missing values are based on the train-only median.
    if raw_train["income"].isna().any():
        assert expected_median in train[:, 0]
    if raw_test["income"].isna().any():
        assert expected_median in test[:, 0]


def test_unknown_categorical_value_does_not_require_leaking_test_categories():
    df = pd.DataFrame({
        "sector": ["a", "b", "c", "a", "b", "c", "a", "b", "c", "rare"],
        "target": list(range(10)),
    })
    train, test, _, _, _, names = prepare_holdout(
        df, "target", "regression", 0.2, 42
    )
    assert names == ["sector"]
    assert train.shape == (8, 1)
    assert test.shape == (2, 1)
    assert np.isfinite(test).all()


def test_regression_missing_target_must_not_be_replaced_with_zero():
    df = pd.DataFrame({"feature": [1, 2, 3, 4], "target": [1.0, None, 3.0, 4.0]})
    with pytest.raises(ValueError, match="Missing target"):
        prepare_holdout(df, "target", "regression", 0.25, 42)


def test_invalid_target_is_rejected():
    df = pd.DataFrame({"value": [1, 2, 3, 4], "label": [0, 1, 0, 1]})
    with pytest.raises(ValueError, match="Target column"):
        prepare_holdout(df, "missing", "classification", 0.25, 42)
