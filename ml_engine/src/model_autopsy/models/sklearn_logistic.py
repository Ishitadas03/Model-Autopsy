"""Logistic Regression model adapter with training-isolated feature scaling for Model Autopsy."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass
class LogisticRegressionConfig:
    """Hyperparameters and configuration for LogisticRegressionAdapter."""

    penalty: str = "l2"
    C: float = 1.0
    solver: str = "lbfgs"
    max_iter: int = 1000
    random_state: Optional[int] = 42
    with_mean: bool = True
    with_std: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to serializable dictionary."""
        return asdict(self)


class LogisticRegressionAdapter:
    """Standardized model adapter wrapping scikit-learn's LogisticRegression in a Pipeline with StandardScaler.

    Scientific Rationale:
        Linear models are sensitive to relative feature scales because L2 weight regularization
        penalizes coefficients symmetrically. To guarantee zero data leakage, feature scaling
        (StandardScaler) is strictly encapsulated in an explicit Pipeline and fitted exclusively
        on training instances. During inference on corrupted test instances, the frozen training-derived
        scaling parameters (mean and std) are applied without fitting or updating on test data.
    """

    def __init__(self, config: Optional[LogisticRegressionConfig] = None, seed: Optional[int] = None):
        if config is None:
            config = LogisticRegressionConfig()
        if seed is not None:
            config.random_state = seed

        self.config = config
        self._scaler = StandardScaler(
            with_mean=self.config.with_mean,
            with_std=self.config.with_std,
        )
        kwargs = {
            "C": self.config.C,
            "solver": self.config.solver,
            "max_iter": self.config.max_iter,
            "random_state": self.config.random_state,
        }
        if self.config.penalty not in (None, "l2"):
            kwargs["penalty"] = self.config.penalty
        self._classifier = LogisticRegression(**kwargs)
        self._pipeline = Pipeline([
            ("scaler", self._scaler),
            ("classifier", self._classifier),
        ])
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        """Indicate whether the underlying pipeline has been fitted."""
        return self._is_fitted

    @property
    def scaler(self) -> StandardScaler:
        """Access the underlying StandardScaler instance."""
        return self._scaler

    @property
    def classifier(self) -> LogisticRegression:
        """Access the underlying LogisticRegression estimator."""
        return self._classifier

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LogisticRegressionAdapter":
        """Fit the StandardScaler and LogisticRegression classifier strictly on training observations.

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

        self._pipeline.fit(X, y)
        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels for evaluation instances using frozen training-fitted scaling.

        Args:
            X: Input feature matrix (n_samples, n_features).

        Returns:
            Predicted class labels (n_samples,).
        """
        if not self._is_fitted:
            raise RuntimeError("ModelAdapter has not been fitted. Call fit() before predict().")
        if X.ndim != 2:
            raise ValueError(f"Expected 2D feature matrix, got shape {X.shape}")

        return self._pipeline.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities for evaluation instances using frozen training-fitted scaling.

        Args:
            X: Input feature matrix (n_samples, n_features).

        Returns:
            Class probability matrix (n_samples, n_classes).
        """
        if not self._is_fitted:
            raise RuntimeError("ModelAdapter has not been fitted. Call fit() before predict_proba().")
        if X.ndim != 2:
            raise ValueError(f"Expected 2D feature matrix, got shape {X.shape}")

        return self._pipeline.predict_proba(X)

    def get_params(self) -> Dict[str, Any]:
        """Retrieve model configuration and fitted pipeline parameters."""
        params = self.config.to_dict()
        params["is_fitted"] = self._is_fitted
        if self._is_fitted:
            params["scaler_mean"] = [float(v) for v in self._scaler.mean_]
            params["scaler_scale"] = [float(v) for v in self._scaler.scale_]
            params["n_iter"] = [int(v) for v in getattr(self._classifier, "n_iter_", [])]
        return params
