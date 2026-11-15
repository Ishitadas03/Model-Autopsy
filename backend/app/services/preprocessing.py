"""Leakage-safe tabular holdout preparation shared by baseline and stress runner.

Feature transformations are fitted only on training samples. The returned
matrix columns are ordered numeric first, categorical second, matching names.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder


def prepare_holdout(
    df: pd.DataFrame,
    target_column: str,
    task_type: str,
    test_size: float,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str], List[str]]:
    if target_column not in df.columns:
        raise ValueError(f"Target column {target_column!r} not found")
    if task_type not in ("classification", "regression"):
        raise ValueError(f"Unsupported task type: {task_type}")
    if not 0.05 <= test_size <= 0.50:
        raise ValueError("test_size must be between 0.05 and 0.50")
    if df.empty or len(df.columns) < 2:
        raise ValueError("A dataset must have rows and at least one feature column")
    if not df.columns.is_unique:
        raise ValueError("Duplicate column names are not supported")

    X = df.drop(columns=[target_column])
    y = df[target_column]
    if y.isna().any():
        raise ValueError("Missing target values cannot be used for supervised evaluation")
    if task_type == "classification":
        labels = LabelEncoder()
        target = labels.fit_transform(y.astype(str))
        classes = [str(label) for label in labels.classes_]
        if len(classes) < 2:
            raise ValueError("Classification requires at least two distinct classes")
    else:
        numeric_target = pd.to_numeric(y, errors="coerce")
        if numeric_target.isna().any() or not np.isfinite(numeric_target.to_numpy()).all():
            raise ValueError("Regression targets must be finite numeric values")
        target = numeric_target.to_numpy(dtype=np.float64)
        classes = []

    numeric_cols = list(X.select_dtypes(include=[np.number]).columns)
    categorical_cols = [col for col in X.columns if col not in numeric_cols]
    feature_names = numeric_cols + categorical_cols

    stratify = None
    if task_type == "classification":
        counts = np.bincount(target)
        if np.all(counts >= 2):
            stratify = target

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, target, test_size=test_size, random_state=seed, stratify=stratify,
    )
    transformers = []
    if numeric_cols:
        transformers.append((
            "numeric",
            Pipeline([("imputer", SimpleImputer(strategy="median", keep_empty_features=True))]),
            numeric_cols,
        ))
    if categorical_cols:
        transformers.append((
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
                ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
            ]),
            categorical_cols,
        ))
    transformer = ColumnTransformer(transformers, remainder="drop", sparse_threshold=0.0)
    X_train = np.asarray(transformer.fit_transform(X_train_raw), dtype=np.float64)
    X_test = np.asarray(transformer.transform(X_test_raw), dtype=np.float64)
    if not np.isfinite(X_train).all() or not np.isfinite(X_test).all():
        raise ValueError("Non-finite feature values remain after preprocessing")
    return X_train, X_test, np.asarray(y_train), np.asarray(y_test), classes, feature_names
