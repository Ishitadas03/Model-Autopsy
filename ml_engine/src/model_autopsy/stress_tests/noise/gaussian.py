"""Additive Gaussian noise perturbation stress test for Model Autopsy."""

from dataclasses import dataclass
from typing import Any, Dict, Optional
import numpy as np


@dataclass(frozen=True)
class PerturbationResult:
    """Container holding the corrupted feature matrix and audit metadata."""

    X_corrupted: np.ndarray
    severity: float
    noise_seed: Optional[int]
    noise_matrix: np.ndarray
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        """Enforce read-only guarantees on output arrays."""
        self.X_corrupted.flags.writeable = False
        self.noise_matrix.flags.writeable = False


def apply_gaussian_noise(
    X: np.ndarray,
    train_std: np.ndarray,
    severity: float,
    seed: Optional[int] = None,
) -> PerturbationResult:
    """Apply scale-aware additive Gaussian noise to an evaluation feature matrix.

    Mathematical formulation:
        X'_{ij} = X_{ij} + epsilon_{ij}
        where epsilon_{ij} ~ Normal(0, (severity * train_std[j])^2)

    Guarantees:
        - Severity 0.00 returns an exact copy of X with identical numerical values.
        - The input matrix X is never mutated in-place.
        - train_std must originate strictly from the training partition.
        - Uses isolated PRNG (np.random.default_rng) with explicitly passed seed.

    Args:
        X: Evaluation feature matrix of shape (n_samples, n_features).
        train_std: 1D array of feature standard deviations computed strictly on X_train.
        severity: Dimensionless severity scalar s >= 0.0.
        seed: Deterministic integer seed for Gaussian PRNG draw.

    Returns:
        PerturbationResult containing the corrupted matrix, noise matrix, and metadata.

    Raises:
        ValueError: If severity is negative, arrays are malformed, or dimensions mismatch.
    """
    # 1. Severity validation
    if severity < 0.0:
        raise ValueError(f"Severity must be non-negative (>= 0.0), received {severity}")

    # 2. Input matrix validation
    if not isinstance(X, np.ndarray):
        raise TypeError(f"X must be a numpy ndarray, got {type(X)}")
    if X.ndim != 2:
        raise ValueError(f"X must be a 2D array of shape (n_samples, n_features), got shape {X.shape}")
    if not np.all(np.isfinite(X)):
        raise ValueError("Input feature matrix X contains non-finite values (NaN or Inf)")

    # 3. Training dispersion validation
    if not isinstance(train_std, np.ndarray):
        raise TypeError(f"train_std must be a numpy ndarray, got {type(train_std)}")
    if train_std.ndim != 1:
        raise ValueError(f"train_std must be a 1D array, got shape {train_std.shape}")
    if train_std.shape[0] != X.shape[1]:
        raise ValueError(
            f"Dimension mismatch: train_std has {train_std.shape[0]} features, "
            f"but X has {X.shape[1]} features"
        )
    if not np.all(np.isfinite(train_std)):
        raise ValueError("train_std contains non-finite values (NaN or Inf)")
    if np.any(train_std <= 0):
        raise ValueError("train_std contains non-positive values (<= 0)")

    n_samples, n_features = X.shape

    # 4. Severity 0.00 fast-path: exact unchanged copy
    if severity == 0.0 or abs(severity) < 1e-12:
        noise_matrix = np.zeros_like(X, dtype=np.float64)
        corrupted = X.astype(np.float64, copy=True)
        return PerturbationResult(
            X_corrupted=corrupted,
            severity=0.0,
            noise_seed=seed,
            noise_matrix=noise_matrix,
            metadata={
                "stress_type": "gaussian_noise",
                "severity": 0.0,
                "noise_seed": seed,
                "is_control_baseline": True,
                "mean_absolute_noise": 0.0,
                "max_absolute_noise": 0.0,
            },
        )

    # 5. Stochastic noise draw with deterministic PRNG
    rng = np.random.default_rng(seed)
    feature_scales = severity * train_std  # 1D array of shape (n_features,)

    # Draw epsilon_ij ~ Normal(0, scale_j^2)
    noise_matrix = rng.normal(loc=0.0, scale=feature_scales, size=(n_samples, n_features))
    corrupted = X.astype(np.float64, copy=True) + noise_matrix

    metadata = {
        "stress_type": "gaussian_noise",
        "severity": float(severity),
        "noise_seed": seed,
        "is_control_baseline": False,
        "feature_scales": feature_scales.tolist(),
        "mean_absolute_noise": float(np.mean(np.abs(noise_matrix))),
        "max_absolute_noise": float(np.max(np.abs(noise_matrix))),
    }

    return PerturbationResult(
        X_corrupted=corrupted,
        severity=float(severity),
        noise_seed=seed,
        noise_matrix=noise_matrix,
        metadata=metadata,
    )
