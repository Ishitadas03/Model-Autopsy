"""Integration tests for E001 multi-seed research evaluation suite."""

import csv
import json
from pathlib import Path
import pytest

from model_autopsy.experiments.e001_runner import run_e001_multiseed_experiment


def test_e001_multiseed_pipeline_execution(tmp_path: Path):
    """Tests 1, 2, 11: Multi-seed execution across all 5 seeds and all 7 severities with schema validation."""
    out_dir = tmp_path / "artifacts_multiseed"
    expected_seeds = [42, 123, 456, 789, 1011]
    expected_severities = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]

    res = run_e001_multiseed_experiment(
        seeds=expected_seeds,
        output_dir=out_dir,
    )

    assert res["status"] == "success"
    assert res["n_successful_seeds"] == 5
    assert res["n_failed_seeds"] == 0

    m_res = res["multi_seed_result"]

    # Test 1: All 5 seeds are represented
    assert m_res.seeds == expected_seeds
    assert len(m_res.per_seed_results) == 5

    # Test 2: Every configured severity is evaluated for each seed
    for s_val in expected_seeds:
        run_data = m_res.per_seed_results[s_val]
        run_sevs = [r["severity"] for r in run_data["severity_records"]]
        assert run_sevs == expected_severities

    # Test 11: Schema validation of generated artifacts
    artifacts = res["artifacts"]

    # 1. all_seeds_results.csv
    csv_file = Path(artifacts["all_seeds_results.csv"])
    assert csv_file.exists()
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        # 5 seeds * 7 severities = 35 rows
        assert len(reader) == 35
        seeds_found = set(int(r["seed"]) for r in reader)
        assert seeds_found == set(expected_seeds)

    # 2. aggregate_results.csv
    agg_csv = Path(artifacts["aggregate_results.csv"])
    assert agg_csv.exists()
    with open(agg_csv, "r", encoding="utf-8") as f:
        agg_reader = list(csv.DictReader(f))
        assert len(agg_reader) == 7
        for row in agg_reader:
            assert int(row["n_successful_runs"]) == 5
            assert float(row["macro_f1_ci_lower"]) <= float(row["macro_f1_mean"])
            assert float(row["macro_f1_ci_upper"]) >= float(row["macro_f1_mean"])

    # 3. aggregate_results.json
    agg_json = Path(artifacts["aggregate_results.json"])
    assert agg_json.exists()
    with open(agg_json, "r", encoding="utf-8") as f:
        json_data = json.load(f)
        assert len(json_data["severity_aggregates"]) == 7
        assert "boundary_caption" in json_data
        assert "monotonicity_summary" in json_data

    # 4. manifest.json
    manifest = Path(artifacts["manifest.json"])
    assert manifest.exists()
    with open(manifest, "r", encoding="utf-8") as f:
        m_data = json.load(f)
        assert m_data["seeds"]["evaluated_seeds"] == expected_seeds
        assert m_data["statistical_protocol"]["sample_size_R"] == 5
        assert m_data["statistical_protocol"]["t_critical_value"] == pytest.approx(2.7764, abs=1e-3)

    # 5. report.md
    report_file = Path(artifacts["report.md"])
    assert report_file.exists()
    with open(report_file, "r", encoding="utf-8") as f:
        rep_text = f.read()
        assert "Multi-Seed Evaluation" in rep_text
        assert "Sample Size" in rep_text
        assert "$R = 5$" in rep_text
        assert "Student's t" in rep_text
        assert "Observed failure boundary under the specified experimental configuration." in rep_text

    # 6. Plot
    plot_file = Path(artifacts["robustness_curve_multiseed.png"])
    assert plot_file.exists()
    assert plot_file.stat().st_size > 10_000
