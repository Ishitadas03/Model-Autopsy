"""Strict, bounded model adapter parameters for shared/free-tier execution.

Reject unsupported inputs instead of silently ignoring them. The experiment seed
always controls random_state for reproducibility even when a catalog exposes it.
"""
from __future__ import annotations

import math
from typing import Any, Dict


def model_kind(name: str, task_type: str) -> str:
    text = str(name or "").lower()
    if task_type not in {"classification", "regression"}:
        raise ValueError(f"Unsupported supervised task: {task_type}")
    if "random" in text or text.startswith("rf-") or "-rf-" in text:
        return "random_forest"
    if "gradient" in text or "gbm" in text or text.startswith("gb-"):
        return "gradient_boosting"
    if task_type == "classification":
        if "logistic" in text or text.startswith("lr-"):
            return "logistic"
        if "svc" in text or "svm" in text:
            return "svc"
    else:
        if "ridge" in text:
            return "ridge"
        if "linear" in text:
            return "linear"
        if "svr" in text or "svm" in text:
            return "svr"
    raise ValueError(f"No supported {task_type} adapter matches {name!r}")


_VALID = {
    "random_forest": {"n_estimators", "max_depth", "min_samples_split", "random_state"},
    "gradient_boosting": {"n_estimators", "max_depth", "learning_rate", "random_state"},
    "logistic": {"C", "max_iter", "penalty", "solver", "random_state"},
    "svc": {"C", "kernel", "gamma", "random_state"},
    "svr": {"C", "kernel", "gamma"},
    "ridge": {"alpha", "random_state"},
    "linear": {"fit_intercept"},
}
_NUMERIC_LIMITS = {
    "n_estimators": (1, 250, True),
    "max_depth": (1, 24, True),
    "min_samples_split": (2, 30, True),
    "max_iter": (10, 1500, True),
    "random_state": (0, 2147483647, True),
    "C": (0.0001, 100.0, False),
    "learning_rate": (0.0001, 1.0, False),
    "alpha": (0.0, 10000.0, False),
}
_CHOICES = {
    "penalty": {"l2"},
    "solver": {"lbfgs"},
    "kernel": {"rbf"},
    "gamma": {"scale", "auto"},
}


def validate_model_params(name: str, task_type: str, params: Dict[str, Any] | None) -> Dict[str, Any]:
    """Return validated parameters; fail on unknown, enormous or non-finite values."""
    kind = model_kind(name, task_type)
    if params is None:
        return {}
    if not isinstance(params, dict):
        raise ValueError("Model parameters must be an object")
    if len(params) > 12:
        raise ValueError("Too many model parameters")
    invalid = set(params) - _VALID[kind]
    if invalid:
        raise ValueError(f"Unsupported {kind} parameter(s): {sorted(invalid)}")
    result = {}
    for key, raw in params.items():
        if key == "max_depth" and raw is None:
            result[key] = None
            continue
        if key in _NUMERIC_LIMITS:
            low, high, integer = _NUMERIC_LIMITS[key]
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                raise ValueError(f"{key} must be numeric")
            value = float(raw)
            if not math.isfinite(value) or not (low <= value <= high):
                raise ValueError(f"{key} must be finite and within [{low}, {high}]")
            if integer and not value.is_integer():
                raise ValueError(f"{key} must be an integer")
            result[key] = int(value) if integer else value
        elif key in _CHOICES:
            if not isinstance(raw, str) or raw not in _CHOICES[key]:
                raise ValueError(f"Unsupported value for {key}")
            result[key] = raw
        elif key == "fit_intercept":
            if not isinstance(raw, bool):
                raise ValueError("fit_intercept must be true or false")
            result[key] = raw
    return result
