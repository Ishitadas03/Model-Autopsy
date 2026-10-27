"""Canonical enumerations for Model Autopsy API contracts."""

from enum import Enum


class TaskType(str, Enum):
    """Machine learning task type."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class MetricType(str, Enum):
    """Supported evaluation metric types."""

    MACRO_F1 = "f1"
    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    ROC_AUC = "roc_auc"
    PR_AUC = "pr_auc"
    R2 = "r2"
    MAE = "mae"
    RMSE = "rmse"
    LOSS = "loss"


class StressType(str, Enum):
    """Supported stress test and perturbation types."""

    GAUSSIAN_NOISE = "gaussian_noise"
    MISSINGNESS = "missingness"
    OUTLIERS = "outliers"
    FEATURE_CORRUPTION = "feature_corruption"
    DISTRIBUTION_SHIFT = "distribution_shift"


class RunStatus(str, Enum):
    """Lifecycle execution status of an experiment run."""

    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StressMode(str, Enum):
    """Perturbation targeting mode."""

    RANDOM = "random"
    FEATURE_SPECIFIC = "feature_specific"
    STRUCTURED = "structured"
