"""Unit tests for failure boundary detection and empirical sensitivity analysis."""

from model_autopsy.analysis.failure_boundary import (
    MANDATED_BOUNDARY_CAPTION,
    MANDATED_SENSITIVITY_CAVEAT,
    detect_failure_boundary,
)


def test_failure_boundary_detected_at_first_crossing():
    """Verify s* is the minimum severity crossing the threshold."""
    records = [
        {"severity": 0.00, "macro_f1": 0.9667},
        {"severity": 0.05, "macro_f1": 0.9333},
        {"severity": 0.10, "macro_f1": 0.8667},
        {"severity": 0.15, "macro_f1": 0.7667},  # Crosses here!
        {"severity": 0.20, "macro_f1": 0.7000},
        {"severity": 0.25, "macro_f1": 0.6333},
        {"severity": 0.30, "macro_f1": 0.5667},
    ]

    res = detect_failure_boundary(records, failure_threshold=0.80)

    assert res.is_boundary_observed is True
    assert res.observed_boundary == 0.15
    assert res.boundary_caption == MANDATED_BOUNDARY_CAPTION


def test_failure_boundary_unobserved_when_all_pass():
    """Verify s* is reported as unobserved if model remains >= threshold throughout."""
    records = [
        {"severity": 0.00, "macro_f1": 1.0000},
        {"severity": 0.05, "macro_f1": 0.9667},
        {"severity": 0.10, "macro_f1": 0.9333},
        {"severity": 0.15, "macro_f1": 0.9000},
        {"severity": 0.20, "macro_f1": 0.8667},
        {"severity": 0.25, "macro_f1": 0.8333},
        {"severity": 0.30, "macro_f1": 0.8000},  # Exactly 0.8000 -> does NOT fail (< 0.80)
    ]

    res = detect_failure_boundary(records, failure_threshold=0.80)

    assert res.is_boundary_observed is False
    assert res.observed_boundary is None
    assert "s* > 0.30" in res.summary_message
    assert res.boundary_caption == MANDATED_BOUNDARY_CAPTION
