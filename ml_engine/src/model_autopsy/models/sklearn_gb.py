"""Gradient Boosted Decision Trees model adapter for Model Autopsy."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier


@dataclass
class GradientBoostingConfig:
    """Hyperparameters and configuration for GradientBoostingAdapter."""

    n_estimators: int = 100
    learning_rate: float = 0.1
    max_depth: int = 3
    subsample: float = 1.0
    criterion: str = "friedman_mse"
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    random_state: Optional[int] = 42

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to serializable dictionary."""
        return asdict(self)


class GradientBoostingAdapter:
    """Standardized model adapter wrapping scikit-learn's GradientBoostingClassifier.

    Scientific Rationale:
        Gradient Boosted Decision Trees perform forward stagewise additive expansion
        of shallow partition trees to minimize multi-class deviance (log-loss).
        Tree-based partition splits are invariant to monotonic scaling, so raw features
        are used directly without transformation.
    """

    def __init__(self, config: Optional[GradientBoostingConfig] = None, seed: Optional[int] = None):
        if config is None:
            config = GradientBoostingConfig()
        if seed is not None:
            config.random_state = seed

        self.config = config
        gb_kwargs = {
            "n_estimators": self.config.n_estimators,
            "learning_rate": self.config.learning_rate,
            "max_depth": self.config.max_depth,
            "subsample": self.config.subsample,
            "min_samples_split": self.config.min_samples_split,
            "min_samples_leaf": self.config.min_samples_leaf,
            "random_state": self.config.random_state,
        }
        if self.config.criterion not in (None, "friedman_mse"):
            gb_kwargs["criterion"] = self.config.criterion

        self._model = GradientBoostingClassifier(**gb_kwargs)
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        """Indicate whether the underlying estimator has been fitted."""
        return self._is_fitted

    @property
    def model(self) -> GradientBoostingClassifier:
        """Access the underlying GradientBoostingClassifier instance."""
        return self._model

    def fit(self, X: np.ndarray, y: np.ndarray) -> "GradientBoostingAdapter":
        """Fit the Gradient Boosting classifier strictly on training observations.

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
        """Retrieve model configuration parameters."""
        params = self.config.to_dict()
        params["is_fitted"] = self._is_fitted
        if self._is_fitted:
            params["n_estimators_fitted"] = len(self._model.estimators_)
        return params
