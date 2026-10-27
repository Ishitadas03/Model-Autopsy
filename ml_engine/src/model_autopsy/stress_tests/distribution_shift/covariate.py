"""Systematic covariate distribution shift operators for Model Autopsy Experiment E006.

Preregistered implementations of:
1. Directional Affine Translation: X' = X + s * v * sigma_train
2. Covariate Dispersion Inflation: X' = mu_train + (1 + s) * (X - mu_train)
3. Subpopulation Selection Shift: w_i(s) = 1 / (1 + exp(-10 * s * z_i1))
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
import numpy as np
from sklearn.decomposition import PCA


# Canonical unit direction vectors in standardized 4D feature space
DIRECTION_VECTORS: Dict[str, np.ndarray] = {
    "allometric": np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float64),
    "petal_pos": np.array([0.0, 0.0, 1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)], dtype=np.float64),
    "petal_neg": np.array([0.0, 0.0, -1.0 / np.sqrt(2.0), -1.0 / np.sqrt(2.0)], dtype=np.float64),
}


@dataclass(frozen=True)
class TrainDistributionParameters:
    """Encapsulates training-set statistics for strictly isolated distribution shift testing."""

    mean: np.ndarray
    std: np.ndarray
    pca: PCA

    @classmethod
    def fit(cls, X_train: np.ndarray) -> "TrainDistributionParameters":
        """Compute training statistics strictly from the training partition.

        Args:
            X_train: Training feature matrix (n_samples, n_features).

        Returns:
            Fitted TrainDistributionParameters instance.
        """
        if X_train.ndim != 2:
            raise ValueError(f"X_train must be 2D, got shape {X_train.shape}")
        if len(X_train) == 0:
            raise ValueError("X_train cannot be empty")

        mean = np.mean(X_train, axis=0)
        std = np.std(X_train, axis=0, ddof=1)
        # Avoid division by zero on degenerate features
        std = np.where(std < 1e-12, 1.0, std)

        pca = PCA(n_components=1)
        pca.fit(X_train)

        return cls(mean=mean, std=std, pca=pca)


def apply_directional_covariate_shift(
    X: np.ndarray,
    train_std: np.ndarray,
    direction: Union[str, np.ndarray],
    severity: float,
) -> np.ndarray:
    """Apply directional affine translation to test features: X' = X + s * v * sigma_train.

    Args:
        X: Input feature matrix (n_samples, n_features).
        train_std: Feature standard deviations estimated strictly on training data (n_features,).
        direction: Named direction key or explicit unit direction vector (n_features,).
        severity: Dimensionless shift magnitude scalar s in [0.0, 1.0].

    Returns:
        Perturbed feature array X' with writeable=False.
    """
    if not (0.0 <= severity <= 1.0):
        raise ValueError(f"Severity must be in [0.0, 1.0], got {severity}")
    if X.ndim != 2:
        raise ValueError(f"X must be 2D array, got shape {X.shape}")
    if train_std.shape[0] != X.shape[1]:
        raise ValueError(f"train_std length {len(train_std)} != X features {X.shape[1]}")

    # Parse and validate direction vector
    if isinstance(direction, str):
        if direction not in DIRECTION_VECTORS:
            raise KeyError(f"Unknown direction '{direction}'. Available: {list(DIRECTION_VECTORS.keys())}")
        v = DIRECTION_VECTORS[direction]
    else:
        v = np.asarray(direction, dtype=np.float64)
        if v.shape[0] != X.shape[1]:
            raise ValueError(f"Direction vector length {len(v)} != X features {X.shape[1]}")
        norm = np.linalg.norm(v)
        if norm > 1e-12:
            v = v / norm

    # Strict severity-zero bitwise identity
    if severity == 0.0:
        X_out = X.copy()
        X_out.flags.writeable = False
        return X_out

    # Shift displacement: s * v_j * sigma_j
    delta = severity * v * train_std
    X_shifted = X.astype(np.float64) + delta

    X_out = X_shifted.copy()
    X_out.flags.writeable = False
    return X_out


def apply_dispersion_covariate_shift(
    X: np.ndarray,
    train_mean: np.ndarray,
    severity: float,
) -> np.ndarray:
    """Apply radial dispersion dilation outward from training centroid: X' = mu_train + (1 + s) * (X - mu_train).

    Args:
        X: Input feature matrix (n_samples, n_features).
        train_mean: Feature means estimated strictly on training data (n_features,).
        severity: Dimensionless dispersion dilation scalar s in [0.0, 1.0].

    Returns:
        Perturbed feature array X' with writeable=False.
    """
    if not (0.0 <= severity <= 1.0):
        raise ValueError(f"Severity must be in [0.0, 1.0], got {severity}")
    if X.ndim != 2:
        raise ValueError(f"X must be 2D array, got shape {X.shape}")
    if train_mean.shape[0] != X.shape[1]:
        raise ValueError(f"train_mean length {len(train_mean)} != X features {X.shape[1]}")

    # Strict severity-zero bitwise identity
    if severity == 0.0:
        X_out = X.copy()
        X_out.flags.writeable = False
        return X_out

    # Scale deviation from training mean
    scale_factor = 1.0 + severity
    X_dilated = train_mean + scale_factor * (X.astype(np.float64) - train_mean)

    X_out = X_dilated.copy()
    X_out.flags.writeable = False
    return X_out


def compute_selection_shift_weights(
    X: np.ndarray,
    train_pca: PCA,
    severity: float,
    k_scale: float = 10.0,
) -> np.ndarray:
    """Compute subpopulation selection inclusion weights along the 1st principal component.

    Formula:
        w_i(s) = 1 / (1 + exp(-k(s) * z_i1))
        where k(s) = k_scale * s, and z_i1 is the standardized projection on PC1.

    Args:
        X: Input feature matrix (n_samples, n_features).
        train_pca: Fitted PCA object from training data.
        severity: Dimensionless selection severity scalar s in [0.0, 1.0].
        k_scale: Sensitivity scaling constant (default: 10.0).

    Returns:
        1D array of sample weights in (0, 1) with length n_samples.
    """
    if not (0.0 <= severity <= 1.0):
        raise ValueError(f"Severity must be in [0.0, 1.0], got {severity}")
    if X.ndim != 2:
        raise ValueError(f"X must be 2D array, got shape {X.shape}")

    n_samples = len(X)
    # Severity-zero invariant: k(0)=0 -> w_i = 1 / (1 + 1) = 0.5 uniformly
    if severity == 0.0:
        return np.full(n_samples, 0.5, dtype=np.float64)

    # Project onto PC1
    z1 = train_pca.transform(X)[:, 0]
    z1_std = np.std(z1, ddof=1)
    if z1_std > 1e-12:
        z1_norm = (z1 - np.mean(z1)) / z1_std
    else:
        z1_norm = z1

    k = k_scale * severity
    # Numerically stable sigmoid: clip exponent to [-30, 30]
    exponent = np.clip(-k * z1_norm, -30.0, 30.0)
    weights = 1.0 / (1.0 + np.exp(exponent))
    return weights.astype(np.float64)
