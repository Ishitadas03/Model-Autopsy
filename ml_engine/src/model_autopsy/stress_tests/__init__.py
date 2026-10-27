"""Stress testing framework for Model Autopsy."""

from model_autopsy.stress_tests.noise.gaussian import PerturbationResult, apply_gaussian_noise
from model_autopsy.stress_tests.missingness.mcar import apply_feature_missingness_mcar
from model_autopsy.stress_tests.outliers.impulsive import apply_feature_outliers
from model_autopsy.stress_tests.feature_corruption.single_feature import (
    apply_single_feature_gaussian_noise,
    apply_single_feature_missingness,
    apply_single_feature_outliers,
)

from model_autopsy.stress_tests.distribution_shift.covariate import (
    DIRECTION_VECTORS,
    TrainDistributionParameters,
    apply_directional_covariate_shift,
    apply_dispersion_covariate_shift,
    compute_selection_shift_weights,
)

__all__ = [
    "PerturbationResult",
    "apply_gaussian_noise",
    "apply_feature_missingness_mcar",
    "apply_feature_outliers",
    "apply_single_feature_gaussian_noise",
    "apply_single_feature_missingness",
    "apply_single_feature_outliers",
    "DIRECTION_VECTORS",
    "TrainDistributionParameters",
    "apply_directional_covariate_shift",
    "apply_dispersion_covariate_shift",
    "compute_selection_shift_weights",
]
