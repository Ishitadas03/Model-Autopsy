"""Feature outlier contamination perturbation stress test for Model Autopsy."""

from typing import Any, Dict, Optional
import numpy as np

from model_autopsy.stress_tests.noise.gaussian import PerturbationResult


def apply_feature_outliers(
    X: np.ndarray,
    train_mean: np.ndarray,
    train_std: np.ndarray,
    severity: float,
    displacement_factor: float = 5.0,
    seed: Optional[int] = None,
) -> PerturbationResult:
    """Apply impulsive outlier contamination to evaluation features.

    Mathematical formulation:
        For each cell (i, j):
            O_{ij} ~ Bernoulli(severity)
            delta_{ij} ~ Uniform({-1.0, +1.0})
            X'_{ij} = train_mean[j] + delta_{ij} * (displacement_factor * train_std[j])
                      if O_{ij} == 1 else X_{ij}

    Guarantees:
        - Severity 0.00 returns an exact copy of X with identical numerical values.
        - The input matrix X is never mutated in-place.
        - train_mean and train_std must originate strictly from the training partition.
        - Output arrays are read-only to prevent downstream mutations.
        - Uses isolated PRNG (np.random.default_rng) with explicitly passed seed.

    Args:
        X: Evaluation feature matrix of shape (n_samples, n_features).
        train_mean: 1D array of feature means computed strictly on X_train.
        train_std: 1D array of feature standard deviations computed strictly on X_train.
        severity: Contamination probability scalar p_outlier in [0.0, 1.0].
        displacement_factor: Number of training standard deviations away from the mean (default 5.0).
        seed: Deterministic integer seed for PRNG draws.

    Returns:
        PerturbationResult containing corrupted matrix, outlier indicator matrix, and metadata.

    Raises:
        ValueError: If severity is outside [0.0, 1.0], arrays are malformed, or dimensions mismatch.
    """
    # 1. Severity validation
    if severity < 0.0 or severity > 1.0:
        raise ValueError(
            f"Severity (contamination rate) must be in range [0.0, 1.0], received {severity}"
        )
    if displacement_factor <= 0.0:
        raise ValueError(
            f"displacement_factor must be positive (> 0.0), received {displacement_factor}"
        )

    # 2. Input matrix validation
    if not isinstance(X, np.ndarray):
        raise TypeError(f"X must be a numpy ndarray, got {type(X)}")
    if X.ndim != 2:
        raise ValueError(f"X must be a 2D array of shape (n_samples, n_features), got shape {X.shape}")
    if not np.all(np.isfinite(X)):
        raise ValueError("Input feature matrix X contains non-finite values (NaN or Inf)")

    # 3. Training statistics validation
    if not isinstance(train_mean, np.ndarray):
        raise TypeError(f"train_mean must be a numpy ndarray, got {type(train_mean)}")
    if train_mean.ndim != 1 or train_mean.shape[0] != X.shape[1]:
        raise ValueError(f"train_mean must be 1D array of length {X.shape[1]}")
    if not np.all(np.isfinite(train_mean)):
        raise ValueError("train_mean contains non-finite values (NaN or Inf)")

    if not isinstance(train_std, np.ndarray):
        raise TypeError(f"train_std must be a numpy ndarray, got {type(train_std)}")
    if train_std.ndim != 1 or train_std.shape[0] != X.shape[1]:
        raise ValueError(f"train_std must be 1D array of length {X.shape[1]}")
    if not np.all(np.isfinite(train_std)):
        raise ValueError("train_std contains non-finite values (NaN or Inf)")
    if np.any(train_std <= 0):
        raise ValueError("train_std contains non-positive values (<= 0)")

    n_samples, n_features = X.shape

    # 4. Severity 0.00 fast-path: exact unchanged copy
    if severity == 0.0 or abs(severity) < 1e-12:
        outlier_matrix = np.zeros_like(X, dtype=np.float64)
        corrupted = X.astype(np.float64, copy=True)
        return PerturbationResult(
            X_corrupted=corrupted,
            severity=0.0,
            noise_seed=seed,
            noise_matrix=outlier_matrix,
            metadata={
                "stress_type": "feature_outliers",
                "severity": 0.0,
                "noise_seed": seed,
                "is_control_baseline": True,
                "outlier_cells_count": 0,
                "outlier_cells_ratio": 0.0,
                "displacement_factor": float(displacement_factor),
            },
        )

    # 5. Stochastic outlier contamination with deterministic PRNG
    rng = np.random.default_rng(seed)
    # Bernoulli draw for contamination mask
    mask = rng.random(size=(n_samples, n_features)) < severity

    # Uniform sign draw {-1.0, +1.0}
    random_signs = rng.choice(np.array([-1.0, 1.0]), size=(n_samples, n_features))

    corrupted = X.astype(np.float64, copy=True)
    # Calculate outlier replacement values: mu_j + sign * (displacement * sigma_j)
    outlier_values = train_mean + random_signs * (displacement_factor * train_std)

    corrupted[mask] = outlier_values[mask]

    outlier_matrix = mask.astype(np.float64)
    outlier_count = int(np.sum(mask))
    total_cells = n_samples * n_features

    metadata = {
        "stress_type": "feature_outliers",
        "severity": float(severity),
        "noise_seed": seed,
        "is_control_baseline": False,
        "outlier_cells_count": outlier_count,
        "outlier_cells_ratio": float(outlier_count / total_cells),
        "displacement_factor": float(displacement_factor),
    }

    return PerturbationResult(
        X_corrupted=corrupted,
        severity=float(severity),
        noise_seed=seed,
        noise_matrix=outlier_matrix,
        metadata=metadata,
    )
