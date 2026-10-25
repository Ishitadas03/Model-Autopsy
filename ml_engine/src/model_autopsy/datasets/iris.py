"""Iris dataset loader and validation module for Model Autopsy."""

from dataclasses import dataclass
import hashlib
from typing import List, Tuple
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split


@dataclass(frozen=True)
class IrisSplitBundle:
    """Immutable container holding the validated Iris train/test split and training dispersion."""

    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    feature_names: List[str]
    target_names: List[str]
    train_indices: np.ndarray
    test_indices: np.ndarray
    train_std: np.ndarray
    dataset_hash: str
    split_seed: int

    def __post_init__(self) -> None:
        """Enforce read-only guarantees on arrays."""
        self.X_train.flags.writeable = False
        self.X_test.flags.writeable = False
        self.y_train.flags.writeable = False
        self.y_test.flags.writeable = False
        self.train_indices.flags.writeable = False
        self.test_indices.flags.writeable = False
        self.train_std.flags.writeable = False


def compute_array_hash(X: np.ndarray, y: np.ndarray) -> str:
    """Calculate a deterministic SHA-256 fingerprint for dataset arrays."""
    hasher = hashlib.sha256()
    hasher.update(X.tobytes())
    hasher.update(y.tobytes())
    return hasher.hexdigest()


def load_and_validate_iris(
    split_seed: int = 42,
    train_ratio: float = 0.80,
    test_ratio: float = 0.20,
) -> IrisSplitBundle:
    """Load the Iris benchmark dataset, execute strict schema validation,

    and partition into an immutable stratified train/test split.

    Args:
        split_seed: PRNG seed for stratified splitting (frozen to 42 in E001).
        train_ratio: Proportion of instances allocated to training (default 0.80).
        test_ratio: Proportion of instances allocated to testing (default 0.20).

    Returns:
        IrisSplitBundle containing validated, read-only partitions and training dispersion.

    Raises:
        ValueError: If dataset shapes, class balances, or split ratios are invalid.
    """
    if abs((train_ratio + test_ratio) - 1.0) > 1e-6:
        raise ValueError(
            f"Train ratio ({train_ratio}) and test ratio ({test_ratio}) must sum to 1.0"
        )

    raw_iris = load_iris(as_frame=False)
    X = raw_iris.data.astype(np.float64)
    y = raw_iris.target.astype(np.int64)
    feature_names = list(raw_iris.feature_names)
    target_names = list(raw_iris.target_names)

    # 1. Dataset schema checks
    if X.shape != (150, 4):
        raise ValueError(f"Expected Iris features of shape (150, 4), received {X.shape}")
    if y.shape != (150,):
        raise ValueError(f"Expected Iris targets of shape (150,), received {y.shape}")
    if len(feature_names) != 4:
        raise ValueError(f"Expected 4 feature names, received {len(feature_names)}")
    if len(target_names) != 3:
        raise ValueError(f"Expected 3 target class names, received {len(target_names)}")

    # 2. Nullity and finiteness checks
    if not np.all(np.isfinite(X)):
        raise ValueError("Iris features contain non-finite values (NaN or Inf)")
    if not np.all(np.isfinite(y)):
        raise ValueError("Iris targets contain non-finite values")

    # 3. Class balance check: exactly 50 instances per class
    unique_classes, counts = np.unique(y, return_counts=True)
    if not np.array_equal(unique_classes, np.array([0, 1, 2])):
        raise ValueError(f"Expected target classes [0, 1, 2], found {unique_classes}")
    if not np.all(counts == 50):
        raise ValueError(f"Expected exactly 50 samples per class, found {counts}")

    # Compute full dataset SHA-256 fingerprint
    dataset_hash = compute_array_hash(X, y)

    # 4. Stratified train/test partitioning
    indices = np.arange(len(y))
    train_idx, test_idx, y_train, y_test = train_test_split(
        indices,
        y,
        test_size=test_ratio,
        stratify=y,
        random_state=split_seed,
    )

    X_train = X[train_idx].copy()
    X_test = X[test_idx].copy()

    # 5. Partition validation
    if len(train_idx) != 120 or len(test_idx) != 30:
        raise ValueError(
            f"Expected 120 train and 30 test samples, got {len(train_idx)} and {len(test_idx)}"
        )

    # Zero overlap audit
    overlap = set(train_idx).intersection(set(test_idx))
    if len(overlap) > 0:
        raise ValueError(f"Fatal data leakage: {len(overlap)} samples overlap between train and test!")

    # Verify per-class balance in partitions (40 train, 10 test per class)
    _, train_counts = np.unique(y_train, return_counts=True)
    _, test_counts = np.unique(y_test, return_counts=True)
    if not np.all(train_counts == 40):
        raise ValueError(f"Expected 40 samples per class in training set, got {train_counts}")
    if not np.all(test_counts == 10):
        raise ValueError(f"Expected 10 samples per class in test set, got {test_counts}")

    # 6. Feature Dispersion: Sample standard deviation calculated strictly on X_train (ddof=1)
    train_std = np.std(X_train, axis=0, ddof=1)
    if np.any(train_std <= 0):
        raise ValueError("Calculated zero or negative standard deviation on training features")

    return IrisSplitBundle(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        feature_names=feature_names,
        target_names=target_names,
        train_indices=train_idx,
        test_indices=test_idx,
        train_std=train_std,
        dataset_hash=dataset_hash,
        split_seed=split_seed,
    )
