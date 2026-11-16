"""Real CSV regression/classification smoke tests: no demo data, no false metrics."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml


@pytest.mark.parametrize(
    "task,metric,n_classes",
    [("classification", "f1", 2), ("classification", "accuracy", 3),
     ("regression", "r2", 0), ("regression", "mae", 0)],
)
def test_custom_csv_generic_workflow(tmp_path, task, metric, n_classes):
    rng = np.random.default_rng(17)
    n = 90
    x = rng.normal(size=n)
    data = {"feature_a": x, "feature_b": x ** 2 + rng.normal(0, .2, n)}
    if task == "classification":
        data["target"] = np.arange(n) % n_classes
    else:
        data["target"] = 2 * x + rng.normal(0, .25, n)
    csv_path = tmp_path / "custom.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)

    config = {
        "experiment": {
            "name": "test-experiment",
            "task_type": task,
            "model": {"name": "RandomForest", "hyperparameters": {"n_estimators": 10}},
            "dataset": {
                "id": "custom-dataset",
                "path": str(csv_path),
                "target_column": "target",
                "test_size": 0.25,
            },
            "stress_test": {
                "perturbation_family": "gaussian_noise",
                "severity_levels": [0.0, 0.2],
                "target_features": ["feature_a"],
            },
            "evaluation": {
                "metric": metric,
                "failure_threshold": 0.7 if metric not in {"mae"} else 0.5,
            },
        }
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    output_dir = tmp_path / "output"
    script = Path(__file__).resolve().parents[2] / "scripts" / "experiments" / "run_generic.py"
    result = subprocess.run(
        [sys.executable, str(script), "--config", str(config_path),
         "--output-dir", str(output_dir), "--seeds", "42"],
        text=True, capture_output=True, timeout=45,
    )
    assert result.returncode == 0, result.stderr[-3000:]
    data = json.loads((output_dir / "results.json").read_text(encoding="utf-8"))
    assert metric in data["baseline_metrics"]
    assert metric in data["worst_case_metrics"]
    assert len(data["curve_data"]) == 2
    assert data["metric"] == metric
    assert all(np.isfinite(item["score"]["mean"]) for item in data["severity_aggregates"])
    if task == "regression":
        assert data["baseline_macro_f1"] is None
        assert data["baseline_accuracy"] is None
        assert "mae" in data["worst_case_metrics"]
        assert not data["failed_samples"]
        assert "Macro-F1" not in (output_dir / "report.md").read_text()
    else:
        assert 0 <= data["baseline_metrics"]["f1"] <= 1
        assert "macro_f1" in data["severity_aggregates"][0]
    assert (output_dir / "manifest.json").is_file()
