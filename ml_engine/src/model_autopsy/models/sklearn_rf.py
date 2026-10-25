"""Random Forest model adapter for Model Autopsy."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier


@dataclass
class RandomForestConfig:
    """Hyperparameters and configuration for RandomForestAdapter."""

    n_estimators: int = 100
    max_depth: Optional[int] = None
    criterion: str = "gini"
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    bootstrap: bool = True
    random_state: Optional[int] = 42

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to serializable dictionary."""
        return asdict(self)


class RandomForestAdapter:
    """Standardized model adapter wrapping scikit-learn's RandomForestClassifier."""

    def __init__(self, config: Optional[RandomForestConfig] = None, seed: Optional[int] = None):
        if config is None:
            config = RandomForestConfig()
        if seed is not None:
            config.random_state = seed

        self.config = config
        self._model = RandomForestClassifier(
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            criterion=self.config.criterion,
            min_samples_split=self.config.min_samples_split,
            min_samples_leaf=self.config.min_samples_leaf,
            bootstrap=self.config.bootstrap,
            random_state=self.config.random_state,
        )
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        """Indicate whether the underlying estimator has been fitted."""
        return self._is_fitted

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RandomForestAdapter":
        """Fit the Random Forest classifier on training observations.

        Args:
            X: Training feature matrix (n_samples, n_features).
            y: Training label vector (n_samples,).

        Returns:
            Self instance.
        """
        if X.ndim != 2:
            raise ValueError(f"Expected 2D feature matrix, got shape {X.shape}")
        if y.ndim != 1:
            raise ValueError(f"Expected 1D target vector, got shape {y.shape}")
        if X.shape[0] != y.shape[0]:
            raise ValueError(f"Feature rows ({X.shape[0]}) mismatch target rows ({y.shape[0]})")

        self._model.fit(X, y)
        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels for evaluation instances.

        Args:
            X: Input feature matrix (n_samples, n_features).

        Returns:
            Predicted class labels (n_samples,).
        """
        if not self._is_fitted:
            raise RuntimeError("ModelAdapter has not been fitted. Call fit() before predict().")
        if X.ndim != 2:
            raise ValueError(f"Expected 2D feature matrix, got shape {X.shape}")

        return self._model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities for evaluation instances.

        Args:
            X: Input feature matrix (n_samples, n_features).

        Returns:
            Class probability matrix (n_samples, n_classes).
        """
        if not self._is_fitted:
            raise RuntimeError("ModelAdapter has not been fitted. Call fit() before predict_proba().")
        if X.ndim != 2:
            raise ValueError(f"Expected 2D feature matrix, got shape {X.shape}")

        return self._model.predict_proba(X)

    def get_params(self) -> Dict[str, Any]:
        """Return serializable hyperparameters."""
        return {
            "adapter": "RandomForestAdapter",
            "framework": "scikit-learn",
            "class_name": "RandomForestClassifier",
            "hyperparameters": self.config.to_dict(),
            "is_fitted": self._is_fitted,
        }
