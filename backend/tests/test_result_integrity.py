"""Regression tests: production responses must never manufacture scientific measurements."""
import json
import pytest

from app.services.ml_engine_bridge import MLEngineBridge


def test_missing_artifact_is_an_error(tmp_path):
    with pytest.raises(ValueError, match="no readable results artifact"):
        MLEngineBridge()._parse_results(tmp_path, [42], {"failure_threshold": 0.8})


def test_empty_curve_is_an_error(tmp_path):
    (tmp_path / "results.json").write_text(json.dumps({
        "baseline_macro_f1": 0.9,
        "severity_results": [],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="no measured severity curve"):
        MLEngineBridge()._parse_results(tmp_path, [42], {})


def test_iris_benchmark_results_are_real(tmp_path):
    data = {
        "baseline_macro_f1": 0.8997,
        "baseline_accuracy": 0.9,
        "severity_results": [
            {"severity": 0.0, "macro_f1": 0.8997, "accuracy": 0.9},
            {"severity": 0.3, "macro_f1": 0.8653, "accuracy": 0.8667},
        ],
        "observed_failure_boundary": None,
        "feature_vulnerabilities": [{"feature": "sepal length (cm)", "drop": 0.0}],
    }
    (tmp_path / "results.json").write_text(json.dumps(data), encoding="utf-8")
    parsed = MLEngineBridge()._parse_results(tmp_path, [42], {"failure_threshold": 0.8})
    assert parsed["baseline_macro_f1"] == 0.8997
    assert parsed["worst_case_macro_f1"] == 0.8653
    assert parsed["observed_boundary"] is None
    assert parsed["failed_samples"] == []
    assert parsed["feature_vulnerabilities"] == data["feature_vulnerabilities"]
    assert parsed["curve_data"][1]["accuracy"] == 0.8667


def test_invalid_metric_is_rejected(tmp_path):
    data = {
        "baseline_macro_f1": 0.9,
        "severity_results": [{"severity": 0.0, "macro_f1": "NaN"}],
    }
    (tmp_path / "results.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite metric"):
        MLEngineBridge()._parse_results(tmp_path, [42], {})
