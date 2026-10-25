"""Missing Completely at Random (MCAR) feature perturbation with training-fitted mean imputation."""

from typing import Any, Dict, Optional
import numpy as np

from model_autopsy.stress_tests.noise.gaussian import PerturbationResult


def apply_feature_missingness_mcar(
    X: np.ndarray,
    train_mean: np.ndarray,
    severity: float,
    seed: Optional[int] = None,
) -> PerturbationResult:
    """Apply Missing Completely at Random (MCAR) feature dropout with training mean imputation.

    Mathematical formulation:
        For each cell (i, j):
            M_{ij} ~ Bernoulli(severity)
            X'_{ij} = train_mean[j] if M_{ij} == 1 else X_{ij}

    Guarantees:
        - Severity 0.00 returns an exact copy of X with identical numerical values.
        - The input matrix X is never mutated in-place.
        - train_mean must originate strictly from the training partition.
        - Output arrays are read-only to prevent downstream mutations.
        - Uses isolated PRNG (np.random.default_rng) with explicitly passed seed.

    Args:
        X: Evaluation feature matrix of shape (n_samples, n_features).
        train_mean: 1D array of feature means computed strictly on X_train.
        severity: Missingness probability scalar p_miss in [0.0, 1.0].
        seed: Deterministic integer seed for PRNG Bernoulli draws.

    Returns:
        PerturbationResult containing corrupted matrix, mask matrix, and metadata.

    Raises:
        ValueError: If severity is outside [0.0, 1.0], arrays are malformed, or dimensions mismatch.
    """
    # 1. Severity validation
    if severity < 0.0 or severity > 1.0:
        raise ValueError(
            f"Severity (missingness rate) must be in range [0.0, 1.0], received {severity}"
        )

    # 2. Input matrix validation
    if not isinstance(X, np.ndarray):
        raise TypeError(f"X must be a numpy ndarray, got {type(X)}")
    if X.ndim != 2:
        raise ValueError(f"X must be a 2D array of shape (n_samples, n_features), got shape {X.shape}")
    if not np.all(np.isfinite(X)):
        raise ValueError("Input feature matrix X contains non-finite values (NaN or Inf)")

    # 3. Training mean validation
    if not isinstance(train_mean, np.ndarray):
        raise TypeError(f"train_mean must be a numpy ndarray, got {type(train_mean)}")
    if train_mean.ndim != 1:
        raise ValueError(f"train_mean must be a 1D array, got shape {train_mean.shape}")
    if train_mean.shape[0] != X.shape[1]:
        raise ValueError(
            f"Dimension mismatch: train_mean has {train_mean.shape[0]} features, "
            f"but X has {X.shape[1]} features"
        )
    if not np.all(np.isfinite(train_mean)):
        raise ValueError("train_mean contains non-finite values (NaN or Inf)")

    n_samples, n_features = X.shape

    # 4. Severity 0.00 fast-path: exact unchanged copy
    if severity == 0.0 or abs(severity) < 1e-12:
        mask_matrix = np.zeros_like(X, dtype=np.float64)
        corrupted = X.astype(np.float64, copy=True)
        return PerturbationResult(
            X_corrupted=corrupted,
            severity=0.0,
            noise_seed=seed,
            noise_matrix=mask_matrix,
            metadata={
                "stress_type": "feature_missingness_mcar",
                "severity": 0.0,
                "noise_seed": seed,
                "is_control_baseline": True,
                "missing_cells_count": 0,
                "missing_cells_ratio": 0.0,
                "imputation_strategy": "train_mean",
            },
        )

    # 5. Stochastic MCAR draw with deterministic PRNG
    rng = np.random.default_rng(seed)
    # Bernoulli draw: True if unobserved (dropped)
    mask = rng.random(size=(n_samples, n_features)) < severity

    corrupted = X.astype(np.float64, copy=True)
    # Broadcast train_mean across corrupted matrix where masked
    for j in range(n_features):
        feature_mask = mask[:, j]
        if np.any(feature_mask):
            corrupted[feature_mask, j] = train_mean[j]

    mask_matrix = mask.astype(np.float64)
    missing_count = int(np.sum(mask))
    total_cells = n_samples * n_features

    metadata = {
        "stress_type": "feature_missingness_mcar",
        "severity": float(severity),
        "noise_seed": seed,
        "is_control_baseline": False,
        "missing_cells_count": missing_count,
        "missing_cells_ratio": float(missing_count / total_cells),
        "imputation_strategy": "train_mean",
    }

    return PerturbationResult(
        X_corrupted=corrupted,
        severity=float(severity),
        noise_seed=seed,
        noise_matrix=mask_matrix,
        metadata=metadata,
    )
