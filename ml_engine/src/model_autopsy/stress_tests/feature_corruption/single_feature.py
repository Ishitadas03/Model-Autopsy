"""Coordinate-isolated single-feature perturbation operators for Model Autopsy (RQ3/E005)."""

from typing import Any, Dict, List, Optional
import numpy as np

from model_autopsy.stress_tests.noise.gaussian import PerturbationResult


def apply_single_feature_gaussian_noise(
    X: np.ndarray,
    train_std: np.ndarray,
    feature_index: int,
    severity: float,
    seed: Optional[int] = None,
) -> PerturbationResult:
    """Apply scale-aware additive Gaussian noise isolated strictly to a single feature column.

    Mathematical formulation:
        For target feature j*:
            X'_{ij*} = X_{ij*} + epsilon_i, where epsilon_i ~ Normal(0, (severity * train_std[j*])^2)
        For all other features k != j*:
            X'_{ik} = X_{ik} (bitwise identical)

    Guarantees:
        - Severity 0.00 returns an exact copy of X with identical numerical values.
        - The input matrix X is never mutated in-place.
        - Output arrays are read-only to prevent downstream mutations.
        - train_std must originate strictly from the training partition.
        - Non-target feature columns remain 100% bitwise untouched.
        - Uses isolated PRNG (np.random.default_rng) with explicitly passed seed.

    Args:
        X: Evaluation feature matrix of shape (n_samples, n_features).
        train_std: 1D array of feature standard deviations computed strictly on X_train.
        feature_index: 0-indexed column index j* to perturb.
        severity: Dimensionless severity scalar s >= 0.0.
        seed: Deterministic integer seed for Gaussian PRNG draw.

    Returns:
        PerturbationResult containing the corrupted matrix, noise matrix, and metadata.

    Raises:
        ValueError: If severity is negative, feature_index is out of bounds,
                    arrays are malformed, or dimensions mismatch.
    """
    if severity < 0.0:
        raise ValueError(f"Severity must be non-negative (>= 0.0), received {severity}")

    if not isinstance(X, np.ndarray):
        raise TypeError(f"X must be a numpy ndarray, got {type(X)}")
    if X.ndim != 2:
        raise ValueError(f"X must be a 2D array of shape (n_samples, n_features), got shape {X.shape}")
    if not np.all(np.isfinite(X)):
        raise ValueError("Input feature matrix X contains non-finite values (NaN or Inf)")

    n_samples, n_features = X.shape

    if not isinstance(feature_index, (int, np.integer)):
        raise TypeError(f"feature_index must be an integer, got {type(feature_index)}")
    if feature_index < 0 or feature_index >= n_features:
        raise ValueError(
            f"feature_index {feature_index} is out of bounds for feature matrix with {n_features} features"
        )

    if not isinstance(train_std, np.ndarray):
        raise TypeError(f"train_std must be a numpy ndarray, got {type(train_std)}")
    if train_std.ndim != 1 or train_std.shape[0] != n_features:
        raise ValueError(
            f"train_std must be a 1D array of length {n_features}, got shape {train_std.shape}"
        )
    if not np.all(np.isfinite(train_std)):
        raise ValueError("train_std contains non-finite values (NaN or Inf)")
    if train_std[feature_index] <= 0:
        raise ValueError(f"train_std for feature {feature_index} must be positive (> 0), got {train_std[feature_index]}")

    # Severity 0.00 fast-path: exact unchanged copy
    if severity == 0.0 or abs(severity) < 1e-12:
        noise_matrix = np.zeros_like(X, dtype=np.float64)
        corrupted = X.astype(np.float64, copy=True)
        return PerturbationResult(
            X_corrupted=corrupted,
            severity=0.0,
            noise_seed=seed,
            noise_matrix=noise_matrix,
            metadata={
                "stress_type": "single_feature_gaussian_noise",
                "feature_index": int(feature_index),
                "severity": 0.0,
                "noise_seed": seed,
                "is_control_baseline": True,
                "mean_absolute_noise": 0.0,
                "max_absolute_noise": 0.0,
            },
        )

    # Isolated single-column noise generation
    rng = np.random.default_rng(seed)
    std_j = float(train_std[feature_index])
    scale = float(severity * std_j)
    noise_col = rng.normal(loc=0.0, scale=scale, size=n_samples)

    noise_matrix = np.zeros_like(X, dtype=np.float64)
    noise_matrix[:, feature_index] = noise_col

    corrupted = X.astype(np.float64, copy=True)
    corrupted[:, feature_index] += noise_col

    return PerturbationResult(
        X_corrupted=corrupted,
        severity=float(severity),
        noise_seed=seed,
        noise_matrix=noise_matrix,
        metadata={
            "stress_type": "single_feature_gaussian_noise",
            "feature_index": int(feature_index),
            "severity": float(severity),
            "noise_seed": seed,
            "is_control_baseline": False,
            "mean_absolute_noise": float(np.mean(np.abs(noise_col))),
            "max_absolute_noise": float(np.max(np.abs(noise_col))),
            "theoretical_noise_std": scale,
            "empirical_noise_std": float(np.std(noise_col, ddof=1)) if n_samples > 1 else 0.0,
        },
    )


def apply_single_feature_missingness(
    X: np.ndarray,
    train_mean: np.ndarray,
    feature_index: int,
    severity: float,
    seed: Optional[int] = None,
) -> PerturbationResult:
    """Apply MCAR missingness with training-mean imputation isolated strictly to a single feature column.

    Mathematical formulation:
        For target feature j*:
            M_i ~ Bernoulli(severity)
            X'_{ij*} = train_mean[j*] if M_i == 1 else X_{ij*}
        For all other features k != j*:
            X'_{ik} = X_{ik} (bitwise identical)

    Guarantees:
        - Severity 0.00 returns an exact copy of X with identical numerical values.
        - The input matrix X is never mutated in-place.
        - Output arrays are read-only.
        - train_mean must originate strictly from the training partition.
        - Non-target feature columns remain 100% bitwise untouched.
        - Uses isolated PRNG (np.random.default_rng) with explicitly passed seed.

    Args:
        X: Evaluation feature matrix of shape (n_samples, n_features).
        train_mean: 1D array of feature means computed strictly on X_train.
        feature_index: 0-indexed column index j* to perturb.
        severity: Missingness probability scalar p_miss in [0.0, 1.0].
        seed: Deterministic integer seed for PRNG Bernoulli draws.

    Returns:
        PerturbationResult containing corrupted matrix, mask matrix, and metadata.
    """
    if severity < 0.0 or severity > 1.0:
        raise ValueError(
            f"Severity (missingness rate) must be in range [0.0, 1.0], received {severity}"
        )

    if not isinstance(X, np.ndarray):
        raise TypeError(f"X must be a numpy ndarray, got {type(X)}")
    if X.ndim != 2:
        raise ValueError(f"X must be a 2D array of shape (n_samples, n_features), got shape {X.shape}")
    if not np.all(np.isfinite(X)):
        raise ValueError("Input feature matrix X contains non-finite values (NaN or Inf)")

    n_samples, n_features = X.shape

    if not isinstance(feature_index, (int, np.integer)):
        raise TypeError(f"feature_index must be an integer, got {type(feature_index)}")
    if feature_index < 0 or feature_index >= n_features:
        raise ValueError(
            f"feature_index {feature_index} is out of bounds for feature matrix with {n_features} features"
        )

    if not isinstance(train_mean, np.ndarray):
        raise TypeError(f"train_mean must be a numpy ndarray, got {type(train_mean)}")
    if train_mean.ndim != 1 or train_mean.shape[0] != n_features:
        raise ValueError(
            f"train_mean must be a 1D array of length {n_features}, got shape {train_mean.shape}"
        )
    if not np.all(np.isfinite(train_mean)):
        raise ValueError("train_mean contains non-finite values (NaN or Inf)")

    # Severity 0.00 fast-path
    if severity == 0.0 or abs(severity) < 1e-12:
        mask_matrix = np.zeros_like(X, dtype=np.float64)
        corrupted = X.astype(np.float64, copy=True)
        return PerturbationResult(
            X_corrupted=corrupted,
            severity=0.0,
            noise_seed=seed,
            noise_matrix=mask_matrix,
            metadata={
                "stress_type": "single_feature_missingness",
                "feature_index": int(feature_index),
                "severity": 0.0,
                "noise_seed": seed,
                "is_control_baseline": True,
                "missing_cells_count": 0,
                "missing_cells_ratio": 0.0,
                "imputation_strategy": "train_mean",
            },
        )

    rng = np.random.default_rng(seed)
    mask_col = rng.random(size=n_samples) < severity

    mask_matrix = np.zeros_like(X, dtype=np.float64)
    mask_matrix[mask_col, feature_index] = 1.0

    corrupted = X.astype(np.float64, copy=True)
    corrupted[mask_col, feature_index] = train_mean[feature_index]

    return PerturbationResult(
        X_corrupted=corrupted,
        severity=float(severity),
        noise_seed=seed,
        noise_matrix=mask_matrix,
        metadata={
            "stress_type": "single_feature_missingness",
            "feature_index": int(feature_index),
            "severity": float(severity),
            "noise_seed": seed,
            "is_control_baseline": False,
            "missing_cells_count": int(np.sum(mask_col)),
            "missing_cells_ratio": float(np.mean(mask_col)),
            "imputation_strategy": "train_mean",
        },
    )


def apply_single_feature_outliers(
    X: np.ndarray,
    train_mean: np.ndarray,
    train_std: np.ndarray,
    feature_index: int,
    severity: float,
    displacement_factor: float = 5.0,
    seed: Optional[int] = None,
) -> PerturbationResult:
    """Apply impulsive outlier contamination isolated strictly to a single feature column.

    Mathematical formulation:
        For target feature j*:
            O_i ~ Bernoulli(severity)
            delta_i ~ Uniform({-1.0, +1.0})
            X'_{ij*} = train_mean[j*] + delta_i * (displacement_factor * train_std[j*])
                       if O_i == 1 else X_{ij*}
        For all other features k != j*:
            X'_{ik} = X_{ik} (bitwise identical)

    Guarantees:
        - Severity 0.00 returns an exact copy of X with identical numerical values.
        - The input matrix X is never mutated in-place.
        - Output arrays are read-only.
        - train_mean and train_std must originate strictly from the training partition.
        - Non-target feature columns remain 100% bitwise untouched.
        - Uses isolated PRNG (np.random.default_rng) with explicitly passed seed.

    Args:
        X: Evaluation feature matrix of shape (n_samples, n_features).
        train_mean: 1D array of feature means computed strictly on X_train.
        train_std: 1D array of feature standard deviations computed strictly on X_train.
        feature_index: 0-indexed column index j* to perturb.
        severity: Contamination probability scalar p_outlier in [0.0, 1.0].
        displacement_factor: Number of training standard deviations away from the mean (default 5.0).
        seed: Deterministic integer seed for PRNG draws.

    Returns:
        PerturbationResult containing corrupted matrix, outlier indicator matrix, and metadata.
    """
    if severity < 0.0 or severity > 1.0:
        raise ValueError(
            f"Severity (contamination rate) must be in range [0.0, 1.0], received {severity}"
        )
    if displacement_factor <= 0.0:
        raise ValueError(
            f"displacement_factor must be positive (> 0.0), received {displacement_factor}"
        )

    if not isinstance(X, np.ndarray):
        raise TypeError(f"X must be a numpy ndarray, got {type(X)}")
    if X.ndim != 2:
        raise ValueError(f"X must be a 2D array of shape (n_samples, n_features), got shape {X.shape}")
    if not np.all(np.isfinite(X)):
        raise ValueError("Input feature matrix X contains non-finite values (NaN or Inf)")

    n_samples, n_features = X.shape

    if not isinstance(feature_index, (int, np.integer)):
        raise TypeError(f"feature_index must be an integer, got {type(feature_index)}")
    if feature_index < 0 or feature_index >= n_features:
        raise ValueError(
            f"feature_index {feature_index} is out of bounds for feature matrix with {n_features} features"
        )

    if not isinstance(train_mean, np.ndarray):
        raise TypeError(f"train_mean must be a numpy ndarray, got {type(train_mean)}")
    if train_mean.ndim != 1 or train_mean.shape[0] != n_features:
        raise ValueError(f"train_mean must be 1D array of length {n_features}")
    if not np.all(np.isfinite(train_mean)):
        raise ValueError("train_mean contains non-finite values (NaN or Inf)")

    if not isinstance(train_std, np.ndarray):
        raise TypeError(f"train_std must be a numpy ndarray, got {type(train_std)}")
    if train_std.ndim != 1 or train_std.shape[0] != n_features:
        raise ValueError(f"train_std must be 1D array of length {n_features}")
    if not np.all(np.isfinite(train_std)):
        raise ValueError("train_std contains non-finite values (NaN or Inf)")
    if train_std[feature_index] <= 0:
        raise ValueError(f"train_std for feature {feature_index} must be positive (> 0)")

    # Severity 0.00 fast-path
    if severity == 0.0 or abs(severity) < 1e-12:
        outlier_matrix = np.zeros_like(X, dtype=np.float64)
        corrupted = X.astype(np.float64, copy=True)
        return PerturbationResult(
            X_corrupted=corrupted,
            severity=0.0,
            noise_seed=seed,
            noise_matrix=outlier_matrix,
            metadata={
                "stress_type": "single_feature_outliers",
                "feature_index": int(feature_index),
                "severity": 0.0,
                "noise_seed": seed,
                "is_control_baseline": True,
                "outlier_cells_count": 0,
                "outlier_cells_ratio": 0.0,
                "displacement_factor": float(displacement_factor),
            },
        )

    rng = np.random.default_rng(seed)
    mask_col = rng.random(size=n_samples) < severity
    # Discrete Rademacher signs: -1.0 or +1.0
    signs_col = rng.choice([-1.0, 1.0], size=n_samples)

    outlier_matrix = np.zeros_like(X, dtype=np.float64)
    outlier_matrix[mask_col, feature_index] = 1.0

    corrupted = X.astype(np.float64, copy=True)
    mu_j = float(train_mean[feature_index])
    std_j = float(train_std[feature_index])
    displacement = float(displacement_factor * std_j)

    corrupted[mask_col, feature_index] = mu_j + signs_col[mask_col] * displacement

    return PerturbationResult(
        X_corrupted=corrupted,
        severity=float(severity),
        noise_seed=seed,
        noise_matrix=outlier_matrix,
        metadata={
            "stress_type": "single_feature_outliers",
            "feature_index": int(feature_index),
            "severity": float(severity),
            "noise_seed": seed,
            "is_control_baseline": False,
            "outlier_cells_count": int(np.sum(mask_col)),
            "outlier_cells_ratio": float(np.mean(mask_col)),
            "displacement_factor": float(displacement_factor),
            "displacement_magnitude": displacement,
        },
    )
