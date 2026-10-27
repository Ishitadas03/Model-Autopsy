"""End-to-end protocol and validation tests for Experiment E006: Systematic Distribution Shift."""

import json
from pathlib import Path
import numpy as np
import pytest

from model_autopsy.analysis.distribution_shift import (
    calculate_audc,
    compute_directional_asymmetry_test,
    compute_dispersion_vs_translation_test,
    compute_friedman_test,
    compute_pairwise_model_tests,
    find_failure_boundary,
)
from model_autopsy.experiments.e006_runner import run_e006_experiment


def test_audc_calculation_known_values():
    """Verify trapezoidal AUDC computation on known linear decay."""
    severities = [0.0, 0.1, 0.2, 0.3]
    # Linear drop from 0 to 30 pp: avg height is 15 pp, width is 0.3 -> area = 4.5
    drops = [0.0, 10.0, 20.0, 30.0]
    audc = calculate_audc(severities, drops)
    assert np.isclose(audc, 4.5, atol=1e-3)


def test_statistical_tests_sanity():
    """Verify Friedman omnibus test and pairwise BH-FDR adjustments."""
    data = {
        "model_a": [10.0, 12.0, 11.0, 10.5, 11.5],
        "model_b": [25.0, 26.0, 24.5, 27.0, 25.5],
        "model_c": [5.0, 6.0, 5.5, 6.5, 5.0],
    }
    f_res = compute_friedman_test(data)
    assert f_res["statistic"] > 0.0
    assert f_res["p_value"] < 0.05
    assert f_res["null_rejected"] is True

    pairwise = compute_pairwise_model_tests(data)
    assert len(pairwise) == 3
    for comp in pairwise:
        assert "adjusted_p_value" in comp
        assert "significant" in comp


def test_directional_asymmetry_test_sanity():
    """Verify directional asymmetry paired testing."""
    pos = [35.0, 36.0, 34.0, 37.0, 35.5]
    neg = [10.0, 11.0, 9.5, 12.0, 10.5]
    res = compute_directional_asymmetry_test(pos, neg)
    assert res["mean_positive_drop"] > res["mean_negative_drop"]
    assert res["null_rejected"] is True


def test_dispersion_vs_translation_test_sanity():
    """Verify dispersion vs translation comparison."""
    trans = [8.5, 9.0, 8.2, 9.5, 8.8]
    disp = [2.0, 2.5, 1.8, 2.2, 2.1]
    res = compute_dispersion_vs_translation_test(trans, disp)
    assert res["mean_translation_audc"] > res["mean_dispersion_audc"]
    assert res["null_rejected"] is True


def test_e006_complete_execution_and_artifacts(tmp_path):
    """Run E006 in a temporary directory and verify protocol invariants, cell counts, and artifacts."""
    seeds = [42, 123]  # 2 seeds for rapid test execution
    out_dir = tmp_path / "E006"

    result = run_e006_experiment(
        seeds=seeds,
        output_dir=out_dir,
    )

    assert result["status"] == "COMPLETED"
    # 3 models x 5 regimes x 7 severities x 2 seeds = 210 cells
    expected_cells = 3 * 5 * 7 * len(seeds)
    assert result["total_evaluation_cells"] == expected_cells

    # Check that all expected artifact files exist and are non-empty
    expected_files = [
        "metrics.json",
        "shift_summary.csv",
        "shift_comparisons.json",
        "reproducibility_manifest.json",
        "report.md",
        "figures/covariate_shift_curves.png",
        "figures/directional_asymmetry_bars.png",
        "figures/shift_vs_corruption_comparison.png",
    ]
    for rel_path in expected_files:
        p = out_dir / rel_path
        assert p.exists(), f"Missing artifact: {rel_path}"
        assert p.stat().st_size > 0, f"Empty artifact: {rel_path}"

    # Verify metrics.json schema
    with open(out_dir / "metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)
    assert metrics["experiment_id"] == "E006"
    assert len(metrics["cell_records"]) == expected_cells

    # Verify baseline parity at severity 0.00: absolute_degradation_pp must be 0.0
    for rec in metrics["cell_records"]:
        if rec["severity"] == 0.0:
            assert rec["absolute_degradation_pp"] == 0.0, (
                f"Baseline parity failed for {rec['model']} under {rec['shift_regime']} at seed {rec['seed']}"
            )

    # Verify shift_comparisons.json schema
    with open(out_dir / "shift_comparisons.json", "r", encoding="utf-8") as f:
        comps = json.load(f)
    assert "hypothesis_tests" in comps
    assert "h1_friedman" in comps["hypothesis_tests"]
    assert "h2_asymmetry" in comps["hypothesis_tests"]
    assert "h3_shift_vs_noise" in comps["hypothesis_tests"]
    assert "h4_dispersion_vs_translation" in comps["hypothesis_tests"]

    # Verify report.md contains mandatory disclaimers
    with open(out_dir / "report.md", "r", encoding="utf-8") as f:
        report_text = f.read()
    assert "Observed failure boundary under the specified experimental configuration" in report_text
    assert "Distribution shift trajectories reflect empirical model sensitivity" in report_text
    assert "Finite Test Resolution" in report_text
    assert "Concept Drift Demarcation" in report_text


def test_e006_deterministic_reproducibility(tmp_path):
    """Verify that consecutive executions of E006 produce identical metrics bit-for-bit."""
    out_1 = tmp_path / "run_1"
    out_2 = tmp_path / "run_2"
    seeds = [42]

    res_1 = run_e006_experiment(seeds=seeds, output_dir=out_1)
    res_2 = run_e006_experiment(seeds=seeds, output_dir=out_2)

    with open(out_1 / "metrics.json", "r", encoding="utf-8") as f:
        data_1 = json.load(f)
    with open(out_2 / "metrics.json", "r", encoding="utf-8") as f:
        data_2 = json.load(f)

    # Cell records must match exactly
    assert len(data_1["cell_records"]) == len(data_2["cell_records"])
    for r1, r2 in zip(data_1["cell_records"], data_2["cell_records"]):
        assert r1["model"] == r2["model"]
        assert r1["shift_regime"] == r2["shift_regime"]
        assert r1["severity"] == r2["severity"]
        assert r1["macro_f1"] == r2["macro_f1"]
        assert r1["accuracy"] == r2["accuracy"]
        assert r1["absolute_degradation_pp"] == r2["absolute_degradation_pp"]
