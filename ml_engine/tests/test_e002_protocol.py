"""End-to-end integration and protocol verification tests for experiment E002."""

import csv
import json
from pathlib import Path
import pytest

from model_autopsy.experiments.e002_runner import run_e002_experiment


def test_e002_complete_pipeline_execution(tmp_path: Path):
    """Verify that E002 executes all 3 corruptions across all 5 seeds and generates valid artifacts."""
    seeds = [42, 123, 456, 789, 1011]
    out_dir = tmp_path / "E002_test"

    result = run_e002_experiment(
        seeds=seeds,
        output_dir=out_dir,
    )

    assert result["status"] == "success"
    assert set(result["corruptions_evaluated"]) == {
        "gaussian_noise",
        "feature_missingness_mcar",
        "feature_outliers",
    }

    # 1. Verify primary artifacts exist on disk
    agg_csv = out_dir / "aggregate_comparison.csv"
    agg_json = out_dir / "aggregate_comparison.json"
    plot_png = out_dir / "robustness_comparison.png"
    manifest_json = out_dir / "manifest.json"
    report_md = out_dir / "report.md"

    assert agg_csv.exists(), "aggregate_comparison.csv must be generated"
    assert agg_json.exists(), "aggregate_comparison.json must be generated"
    assert plot_png.exists(), "robustness_comparison.png must be generated"
    assert manifest_json.exists(), "manifest.json must be generated"
    assert report_md.exists(), "report.md must be generated"

    # 2. Validate aggregate_comparison.csv structure
    with open(agg_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    # 3 corruptions * 7 severities = 21 rows
    assert len(reader) == 21, f"Expected 21 rows in comparison CSV, got {len(reader)}"
    for row in reader:
        assert row["corruption"] in {"gaussian_noise", "feature_missingness_mcar", "feature_outliers"}
        assert int(row["n_successful_runs"]) == 5
        mean_f1 = float(row["macro_f1_mean"])
        ci_lower = float(row["macro_f1_ci_lower"])
        ci_upper = float(row["macro_f1_ci_upper"])
        assert ci_lower <= mean_f1 <= ci_upper, "Mean must lie within 95% CI"

    # 3. Validate aggregate_comparison.json schema
    with open(agg_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["experiment_id"] == "E002"
    assert "gaussian_noise" in data["corruptions"]
    assert "feature_missingness_mcar" in data["corruptions"]
    assert "feature_outliers" in data["corruptions"]

    # 4. Validate per-corruption subdirectories
    for corr in ["gaussian_noise", "feature_missingness_mcar", "feature_outliers"]:
        corr_dir = out_dir / "corruptions" / corr
        assert (corr_dir / "aggregate_results.csv").exists()
        assert (corr_dir / "all_seeds_results.csv").exists()
        assert (corr_dir / "aggregate_results.json").exists()

    # 5. Baseline identity check: At s=0.00, all 3 corruptions must report identical mean Macro-F1
    gaussian_s0 = next(r for r in reader if r["corruption"] == "gaussian_noise" and float(r["severity"]) == 0.0)
    mcar_s0 = next(r for r in reader if r["corruption"] == "feature_missingness_mcar" and float(r["severity"]) == 0.0)
    outlier_s0 = next(r for r in reader if r["corruption"] == "feature_outliers" and float(r["severity"]) == 0.0)

    assert float(gaussian_s0["macro_f1_mean"]) == pytest.approx(float(mcar_s0["macro_f1_mean"]), abs=1e-6)
    assert float(gaussian_s0["macro_f1_mean"]) == pytest.approx(float(outlier_s0["macro_f1_mean"]), abs=1e-6)

    # 6. Validate manifest schema
    with open(manifest_json, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["experiment_id"] == "E002"
    assert manifest["evaluation_config"]["primary_metric"] == "macro_f1"
    assert manifest["evaluation_config"]["failure_threshold"] == 0.80
    assert manifest["evaluation_config"]["relative_drop_diagnostic_threshold_pct"] == 15.0

    # 7. Validate markdown report contents
    with open(report_md, "r", encoding="utf-8") as f:
        report_text = f.read()
    assert "Observed failure boundary under the specified experimental configuration." in report_text
    assert "RQ2 Corruption Comparison" in report_text
    assert "Additive Gaussian Noise" in report_text
    assert "MCAR Missingness (Mean Imputed)" in report_text
    assert "Impulsive Outliers (5σ)" in report_text
