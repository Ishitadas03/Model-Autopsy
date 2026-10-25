"""Integration and protocol tests for E004 Failure Pattern Analysis (RQ7)."""

import json
from pathlib import Path
import tempfile
import numpy as np
import pytest

from model_autopsy.analysis.failure_patterns import (
    calculate_error_persistence,
    calculate_exact_binomial_ci,
    calculate_inter_model_concordance,
    calculate_jaccard_similarity,
    calculate_mahalanobis_margins,
    calculate_sample_errors,
    calculate_seed_stability,
)
from model_autopsy.experiments.e004_runner import run_e004_experiment


@pytest.fixture(scope="module")
def e004_execution_result():
    """Execute E004 in a temporary directory with single seed 42 for fast testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_e004_experiment(
            seeds=[42],
            output_dir=Path(tmp_dir),
        )
        yield result


def test_e004_evidence_conservation_identity(e004_execution_result):
    """Test that Evidence Conservation Identity holds strictly."""
    audit = e004_execution_result["evidence_conservation_audit"]
    assert audit["conservation_verified"] is True
    assert len(audit["discrepancies"]) == 0


def test_e004_sample_records_structure(e004_execution_result):
    """Test that atomic prediction records have all required fields and correct counts."""
    # 3 models * 3 corruptions * 1 seed * 7 severities * 30 samples = 1,890 records
    expected_count = 3 * 3 * 1 * 7 * 30
    assert e004_execution_result["n_sample_evaluations"] == expected_count

    artifacts = e004_execution_result["artifacts"]
    pred_path = Path(artifacts["sample_predictions.json"])
    assert pred_path.exists()

    with open(pred_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    assert len(records) == expected_count
    first = records[0]
    required_keys = {
        "sample_id",
        "iris_dataset_index",
        "true_label",
        "true_class_name",
        "model_id",
        "corruption_id",
        "seed",
        "severity",
        "predicted_label",
        "predicted_class_name",
        "is_error",
        "probabilities",
    }
    assert required_keys.issubset(first.keys())
    assert first["sample_id"] in range(30)
    assert first["true_label"] in {0, 1, 2}
    assert isinstance(first["is_error"], bool)


def test_e004_artifacts_exist_and_non_empty(e004_execution_result):
    """Test that all specified E004 artifacts are generated and non-empty."""
    artifacts = e004_execution_result["artifacts"]
    expected_files = [
        "sample_predictions.json",
        "failure_patterns_summary.json",
        "sample_level_metrics.csv",
        "manifest.json",
        "report.md",
        "failure_patterns_analysis.png",
    ]
    for fname in expected_files:
        assert fname in artifacts, f"Missing artifact: {fname}"
        path = Path(artifacts[fname])
        assert path.exists(), f"File does not exist: {path}"
        assert path.stat().st_size > 0, f"File is empty: {path}"


def test_e004_report_contains_mandatory_captions(e004_execution_result):
    """Test that generated report contains verbatim required non-causal captions."""
    artifacts = e004_execution_result["artifacts"]
    report_path = Path(artifacts["report.md"])
    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    assert "Observed failure boundary under the specified experimental configuration." in report_text
    assert "Empirical sensitivity — not a causal explanation." in report_text
    assert "Sample size" in report_text or "N_{test} = 30" in report_text or "N_{\\text{test}} = 30" in report_text


def test_e004_class_vulnerability_asymmetry(e004_execution_result):
    """Test H1 findings: Setosa clean error rate is 0.0% and Versicolor/Virginica share higher vulnerability."""
    summary = e004_execution_result["failure_patterns_summary"]
    trajectories = summary["class_vulnerabilities"]["trajectories"]

    # Setosa has 0.0 clean baseline error rate
    assert trajectories["setosa"][0] == 0.0
    # Setosa remains significantly more resilient than Versicolor and Virginica at maximum severity
    assert trajectories["setosa"][-1] < trajectories["versicolor"][-1]
    assert trajectories["setosa"][-1] < 0.15
    # Versicolor and Virginica experience substantial degradation
    assert trajectories["versicolor"][-1] > 0.15


def test_e004_mahalanobis_margins_sanity(e004_execution_result):
    """Test H4 findings: Mahalanobis margins calculated with strictly train-fitted parameters."""
    summary = e004_execution_result["failure_patterns_summary"]
    margins = summary["feature_space_margins"]

    sample_margins = margins["sample_margins"]
    assert len(sample_margins) == 30

    early_group = margins["early_failing_group"]
    resilient_group = margins["resilient_group"]

    assert early_group["n_samples"] > 0
    assert resilient_group["n_samples"] > 0
    assert early_group["mean_margin"] < resilient_group["mean_margin"]
    assert margins["hypothesis_test"]["caveat"] == "Empirical sensitivity — not a causal explanation."


def test_e004_e003_reproduction_bit_for_bit(e004_execution_result):
    """Test that reconstructed confusion matrices match E003 baseline bit-for-bit."""
    audit = e004_execution_result["evidence_conservation_audit"]
    assert audit["e003_baseline_checks_conducted"] > 0
    assert audit["e003_baseline_matches"] == audit["e003_baseline_checks_conducted"]


def test_e004_persistence_and_absorbing_states(e004_execution_result):
    """Test H2 error persistence bounds and absorbing properties."""
    summary = e004_execution_result["failure_patterns_summary"]
    persist = summary["error_persistence"]

    valid_eprs = persist["valid_eprs"]
    assert len(valid_eprs) > 0
    assert all(0.0 <= epr <= 1.0 for epr in valid_eprs)
    assert persist["mean_error_persistence_ratio"] > 0.80
    assert persist["perfect_persistence_proportion"] > 0.50

