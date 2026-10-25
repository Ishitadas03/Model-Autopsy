"""Comprehensive protocol, integration, and leakage prevention tests for Experiment E003 (RQ5)."""

import csv
import json
from pathlib import Path
import numpy as np
import pytest

from model_autopsy.datasets.iris import load_and_validate_iris
from model_autopsy.experiments.e003_runner import run_e003_experiment
from model_autopsy.models.sklearn_gb import GradientBoostingAdapter, GradientBoostingConfig
from model_autopsy.models.sklearn_logistic import LogisticRegressionAdapter, LogisticRegressionConfig
from model_autopsy.models.sklearn_rf import RandomForestAdapter, RandomForestConfig
from model_autopsy.stress_tests.missingness.mcar import apply_feature_missingness_mcar
from model_autopsy.stress_tests.noise.gaussian import apply_gaussian_noise
from model_autopsy.stress_tests.outliers.impulsive import apply_feature_outliers


def test_model_adapters_instantiation_and_contract():
    """Verify that all three model adapters satisfy the standard Model Autopsy API contract."""
    bundle = load_and_validate_iris(split_seed=42)

    adapters = [
        RandomForestAdapter(RandomForestConfig(n_estimators=10, random_state=42)),
        LogisticRegressionAdapter(LogisticRegressionConfig(max_iter=200, random_state=42)),
        GradientBoostingAdapter(GradientBoostingConfig(n_estimators=10, max_depth=2, random_state=42)),
    ]

    for adapter in adapters:
        # Pre-fit contract
        assert not adapter.is_fitted
        with pytest.raises(RuntimeError):
            adapter.predict(bundle.X_test)
        with pytest.raises(RuntimeError):
            adapter.predict_proba(bundle.X_test)

        # Fit
        adapter.fit(bundle.X_train, bundle.y_train)
        assert adapter.is_fitted

        # Inference shapes
        preds = adapter.predict(bundle.X_test)
        assert preds.shape == (len(bundle.X_test),)
        assert set(preds).issubset({0, 1, 2})

        probs = adapter.predict_proba(bundle.X_test)
        assert probs.shape == (len(bundle.X_test), 3)
        assert np.allclose(probs.sum(axis=1), 1.0)

        # Config extraction
        params = adapter.get_params()
        assert params["is_fitted"] is True


def test_logistic_regression_pipeline_scaling_isolation():
    """Verify that LogisticRegressionAdapter encapsulates StandardScaler strictly on training data without leakage."""
    bundle = load_and_validate_iris(split_seed=42)

    lr_adapter = LogisticRegressionAdapter(LogisticRegressionConfig(max_iter=500, random_state=42))
    lr_adapter.fit(bundle.X_train, bundle.y_train)

    # 1. Scaler parameters must match training data exactly
    expected_mean = np.mean(bundle.X_train, axis=0)
    expected_scale = np.std(bundle.X_train, axis=0, ddof=0)

    np.testing.assert_allclose(lr_adapter.scaler.mean_, expected_mean, rtol=1e-5)
    np.testing.assert_allclose(lr_adapter.scaler.scale_, expected_scale, rtol=1e-5)

    # 2. Frozen state during corrupted inference
    frozen_mean = lr_adapter.scaler.mean_.copy()
    frozen_scale = lr_adapter.scaler.scale_.copy()

    # Corrupt test partition heavily
    X_corrupted = bundle.X_test + 1000.0
    _ = lr_adapter.predict(X_corrupted)

    # Parameters must NOT have mutated or adapted to test distribution
    np.testing.assert_array_equal(lr_adapter.scaler.mean_, frozen_mean)
    np.testing.assert_array_equal(lr_adapter.scaler.scale_, frozen_scale)


def test_shared_split_indices_across_models():
    """Verify that all models are fitted and evaluated on the exact same frozen train/test partition."""
    bundle = load_and_validate_iris(split_seed=42)

    assert len(bundle.X_train) == 120
    assert len(bundle.X_test) == 30
    assert len(set(bundle.train_indices).intersection(set(bundle.test_indices))) == 0

    rf = RandomForestAdapter(RandomForestConfig(random_state=42)).fit(bundle.X_train, bundle.y_train)
    lr = LogisticRegressionAdapter(LogisticRegressionConfig(random_state=42)).fit(bundle.X_train, bundle.y_train)
    gb = GradientBoostingAdapter(GradientBoostingConfig(random_state=42)).fit(bundle.X_train, bundle.y_train)

    # All models produce valid predictions on identical test partition
    p_rf = rf.predict(bundle.X_test)
    p_lr = lr.predict(bundle.X_test)
    p_gb = gb.predict(bundle.X_test)

    assert len(p_rf) == len(p_lr) == len(p_gb) == 30


def test_corruption_compatibility_across_all_models():
    """Verify that all three corruptions can be fed to all three models without NaN or exception."""
    bundle = load_and_validate_iris(split_seed=42)
    train_mean = bundle.train_mean if bundle.train_mean is not None else bundle.X_train.mean(axis=0)

    models = [
        RandomForestAdapter(RandomForestConfig(random_state=42)).fit(bundle.X_train, bundle.y_train),
        LogisticRegressionAdapter(LogisticRegressionConfig(random_state=42)).fit(bundle.X_train, bundle.y_train),
        GradientBoostingAdapter(GradientBoostingConfig(random_state=42)).fit(bundle.X_train, bundle.y_train),
    ]

    corruptions = [
        apply_gaussian_noise(bundle.X_test, bundle.train_std, severity=0.20, seed=42).X_corrupted,
        apply_feature_missingness_mcar(bundle.X_test, train_mean, severity=0.20, seed=42).X_corrupted,
        apply_feature_outliers(bundle.X_test, train_mean, bundle.train_std, severity=0.20, seed=42).X_corrupted,
    ]

    for model in models:
        for X_c in corruptions:
            preds = model.predict(X_c)
            assert preds.shape == (30,)
            assert not np.isnan(preds).any()


def test_e003_complete_pipeline_execution(tmp_path: Path):
    """Integration test: Verify complete E003 execution across 2 seeds and validate all output schemas."""
    seeds = [42, 123]
    out_dir = tmp_path / "E003_test"

    result = run_e003_experiment(
        seeds=seeds,
        output_dir=out_dir,
    )

    assert result["experiment_id"] == "E003"
    assert set(result["models"].keys()) == {"random_forest", "logistic_regression", "gradient_boosting"}

    # 1. Primary artifact existence
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

    # 3 models * 3 corruptions * 7 severities = 63 rows
    assert len(reader) == 63, f"Expected 63 rows in comparison CSV, got {len(reader)}"

    for row in reader:
        assert row["model"] in {"random_forest", "logistic_regression", "gradient_boosting"}
        assert row["corruption"] in {"gaussian_noise", "feature_missingness_mcar", "feature_outliers"}
        assert int(row["n_successful_runs"]) == len(seeds)
        mean_f1 = float(row["macro_f1_mean"])
        ci_lower = float(row["macro_f1_ci_lower"])
        ci_upper = float(row["macro_f1_ci_upper"])
        assert ci_lower <= mean_f1 <= ci_upper, "Mean must lie within 95% CI"

    # 3. Validate aggregate_comparison.json
    with open(agg_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["experiment_id"] == "E003"
    assert "random_forest" in data["models"]
    assert "logistic_regression" in data["models"]
    assert "gradient_boosting" in data["models"]

    # 4. Validate per-model directories
    for m in ["random_forest", "logistic_regression", "gradient_boosting"]:
        m_dir = out_dir / "models" / m
        assert (m_dir / "aggregate_results.csv").exists()
        for corr in ["gaussian_noise", "feature_missingness_mcar", "feature_outliers"]:
            c_dir = m_dir / "corruptions" / corr
            assert (c_dir / "aggregate_results.csv").exists()
            assert (c_dir / "all_seeds_results.csv").exists()
            assert (c_dir / "aggregate_results.json").exists()

    # 5. Validate manifest
    with open(manifest_json, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["experiment_id"] == "E003"
    assert manifest["evaluation_config"]["failure_threshold"] == 0.80

    # 6. Validate markdown report
    with open(report_md, "r", encoding="utf-8") as f:
        report_text = f.read()
    assert "Observed failure boundary under the specified experimental configuration." in report_text
    assert "Empirical sensitivity — not a causal explanation." in report_text
    assert "RQ5 Model Robustness Comparison" in report_text
    assert "Random Forest" in report_text
    assert "Logistic Regression" in report_text
    assert "Gradient Boosting" in report_text
