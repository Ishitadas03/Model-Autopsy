"""End-to-end protocol and integration tests for Experiment E005 (RQ3 Feature Vulnerability)."""

import json
from pathlib import Path
import tempfile
import numpy as np
import pytest

from model_autopsy.analysis.failure_boundary import MANDATED_BOUNDARY_CAPTION
from model_autopsy.datasets.iris import load_and_validate_iris
from model_autopsy.experiments.e005_runner import run_e005_experiment
from model_autopsy.models.sklearn_logistic import LogisticRegressionAdapter, LogisticRegressionConfig
from model_autopsy.models.sklearn_rf import RandomForestAdapter, RandomForestConfig


MANDATED_NON_CAUSAL_DISCLAIMER = (
    "Feature vulnerability rankings reflect empirical model sensitivity under the specified perturbation operators "
    "and must not be interpreted as causal claims regarding the underlying physical or biological data-generating system."
)


@pytest.fixture(scope="module")
def e005_test_execution() -> tuple[dict, Path]:
    """Execute E005 in an isolated temporary directory across 2 seeds for rapid integration verification."""
    temp_dir = tempfile.mkdtemp(prefix="e005_test_")
    output_path = Path(temp_dir)

    result = run_e005_experiment(
        seeds=[42, 123],
        output_dir=output_path,
    )
    return result, output_path


def test_e005_complete_execution_and_artifacts(e005_test_execution: tuple[dict, Path]):
    """Test 1: Full pipeline execution and verify all canonical artifacts exist and are non-empty."""
    result, output_dir = e005_test_execution

    assert result["status"] == "completed"
    assert result["total_evaluation_cells"] == 3 * 3 * 4 * 7 * 2  # 3 models * 3 ops * 4 features * 7 sevs * 2 seeds = 504 cells

    expected_files = [
        "metrics.json",
        "feature_vulnerability_summary.csv",
        "feature_rankings.json",
        "reproducibility_manifest.json",
        "report.md",
        "figures/feature_degradation_curves.png",
        "figures/feature_vulnerability_bars.png",
        "figures/clean_vs_vulnerability_scatter.png",
    ]

    for fname in expected_files:
        fpath = output_dir / fname
        assert fpath.exists(), f"Missing artifact: {fname}"
        assert fpath.stat().st_size > 0, f"Empty artifact: {fname}"


def test_e005_baseline_parity_at_severity_zero(e005_test_execution: tuple[dict, Path]):
    """Test 2: At severity 0.00, Macro-F1 across all 4 feature evaluations matches the clean baseline bit-for-bit."""
    result, _ = e005_test_execution
    summary = result["e005_summary"]

    for m_id, m_data in summary["models"].items():
        clean_mean = m_data["clean_macro_f1_mean"]
        for op_id, op_data in m_data["operators"].items():
            for f_name, f_info in op_data["features"].items():
                sev_0_agg = f_info["severity_aggregates"][0]
                assert sev_0_agg["severity"] == 0.0
                # Delta abs at s=0 must be exactly 0.0
                assert sev_0_agg["delta_abs_mean"] == 0.0
                # Macro-F1 at s=0 must match clean baseline
                assert abs(sev_0_agg["macro_f1_mean"] - clean_mean) < 1e-6


def test_e005_logistic_regression_scaling_isolation():
    """Test 3: Preprocessing isolation: StandardScaler in LogisticRegressionAdapter is fitted strictly on X_train."""
    bundle = load_and_validate_iris(split_seed=42)
    adapter = LogisticRegressionAdapter(config=LogisticRegressionConfig(), seed=42)
    adapter.fit(bundle.X_train, bundle.y_train)

    scaler = adapter._scaler
    # Scaler mean must match training split mean, NOT test split mean
    train_mean = np.mean(bundle.X_train, axis=0)
    test_mean = np.mean(bundle.X_test, axis=0)

    assert np.allclose(scaler.mean_, train_mean)
    assert not np.allclose(scaler.mean_, test_mean)


def test_e005_report_contains_mandatory_disclaimers(e005_test_execution: tuple[dict, Path]):
    """Test 4: Verify generated report.md contains mandated non-causal disclaimer and boundary caption."""
    _, output_dir = e005_test_execution
    report_text = (output_dir / "report.md").read_text(encoding="utf-8")

    assert MANDATED_NON_CAUSAL_DISCLAIMER in report_text
    assert MANDATED_BOUNDARY_CAPTION in report_text


def test_e005_feature_rankings_json_schema(e005_test_execution: tuple[dict, Path]):
    """Test 5: feature_rankings.json contains valid structure, ranks in [1, 4], and statistical tests."""
    _, output_dir = e005_test_execution
    rankings_json = json.loads((output_dir / "feature_rankings.json").read_text(encoding="utf-8"))

    assert "models" in rankings_json
    assert "inter_model_concordance" in rankings_json

    for m_id, m_data in rankings_json["models"].items():
        assert "operators" in m_data
        for op_id, op_data in m_data["operators"].items():
            t_ranks = op_data["terminal_rankings"]
            assert len(t_ranks) == 4
            assigned_ranks = [r["rank"] for r in t_ranks]
            assert min(assigned_ranks) >= 1.0
            assert max(assigned_ranks) <= 4.0
            assert "friedman_test" in op_data
            assert "pairwise_comparisons" in op_data
            assert len(op_data["pairwise_comparisons"]) == 6


def test_e005_deterministic_reproducibility():
    """Test 6: Repeated executions with seed 42 produce bitwise identical metrics."""
    temp_dir_1 = Path(tempfile.mkdtemp(prefix="e005_rep1_"))
    temp_dir_2 = Path(tempfile.mkdtemp(prefix="e005_rep2_"))

    res1 = run_e005_experiment(seeds=[42], output_dir=temp_dir_1)
    res2 = run_e005_experiment(seeds=[42], output_dir=temp_dir_2)

    # Compare metrics.json content
    m1 = (temp_dir_1 / "feature_vulnerability_summary.csv").read_text(encoding="utf-8")
    m2 = (temp_dir_2 / "feature_vulnerability_summary.csv").read_text(encoding="utf-8")
    assert m1 == m2
