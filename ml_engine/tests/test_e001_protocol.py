"""End-to-end integration and protocol verification tests for Experiment E001."""

import csv
import json
from pathlib import Path
import pytest
from model_autopsy.experiments.e001_runner import run_e001_experiment


def test_e001_complete_execution_and_artifacts(tmp_path: Path):
    """Tests 19, 20, 21: Full pipeline execution, grid completeness, and artifact generation."""
    config_path = Path("configs/experiments/e001.yaml")
    out_dir = tmp_path / "artifacts"

    result = run_e001_experiment(
        config_path=config_path,
        seed=42,
        output_dir=out_dir,
    )

    # 1. Pipeline status
    assert result["status"] == "success"
    assert result["experiment_id"] == "E001"

    # 2. Test 19: Every configured severity is evaluated
    expected_severities = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    evaluated_severities = [r["severity"] for r in result["severity_records"]]
    assert evaluated_severities == expected_severities

    # Baseline severity s=0.00 exact metrics
    baseline_rec = result["severity_records"][0]
    assert baseline_rec["severity"] == 0.00
    assert baseline_rec["absolute_degradation_pp"] == 0.0
    assert baseline_rec["relative_degradation_pct"] == 0.0

    # 3. Test 20: Check artifact existence and validity
    artifacts = result["artifacts"]

    # results.csv
    csv_file = Path(artifacts["results.csv"])
    assert csv_file.exists()
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 7
        assert float(reader[0]["severity"]) == 0.00

    # results.json
    res_json_file = Path(artifacts["results.json"])
    assert res_json_file.exists()
    with open(res_json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["experiment_id"] == "E001"
        assert len(data["severity_results"]) == 7

    # manifest.json
    manifest_file = Path(artifacts["manifest.json"])
    assert manifest_file.exists()
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        assert manifest["experiment_id"] == "E001"
        assert manifest["seeds"]["model_seed"] == 42
        assert manifest["seeds"]["split_seed"] == 42
        assert "git_commit_hash" in manifest
        assert "environment" in manifest

    # report.md
    report_file = Path(artifacts["report.md"])
    assert report_file.exists()
    with open(report_file, "r", encoding="utf-8") as f:
        report_text = f.read()
        assert "# Empirical Research Report: E001" in report_text
        assert "Observed failure boundary under the specified experimental configuration." in report_text
        assert "Empirical sensitivity — not a causal explanation." in report_text

    # 4. Test 21: Robustness curve PNG generated and non-empty
    plot_file = Path(artifacts["robustness_curve.png"])
    assert plot_file.exists()
    assert plot_file.stat().st_size > 10_000  # Non-empty high-res image


def test_e001_deterministic_reproducibility(tmp_path: Path):
    """Test 22: Repeated executions with seed 42 produce bitwise identical scientific metrics."""
    out_dir_1 = tmp_path / "run_1"
    out_dir_2 = tmp_path / "run_2"

    res_1 = run_e001_experiment(seed=42, output_dir=out_dir_1)
    res_2 = run_e001_experiment(seed=42, output_dir=out_dir_2)

    assert res_1["baseline_macro_f1"] == res_2["baseline_macro_f1"]
    assert res_1["baseline_accuracy"] == res_2["baseline_accuracy"]
    assert res_1["failure_boundary"]["observed_boundary"] == res_2["failure_boundary"]["observed_boundary"]

    # Compare all severity records bitwise
    for r1, r2 in zip(res_1["severity_records"], res_2["severity_records"]):
        assert r1["severity"] == r2["severity"]
        assert r1["macro_f1"] == r2["macro_f1"]
        assert r1["accuracy"] == r2["accuracy"]
        assert r1["absolute_degradation_pp"] == r2["absolute_degradation_pp"]
        assert r1["relative_degradation_pct"] == r2["relative_degradation_pct"]
        assert r1["is_failed"] == r2["is_failed"]
        assert r1["confusion_matrix"] == r2["confusion_matrix"]
