"""E001 experiment execution orchestrator."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from model_autopsy.analysis.failure_boundary import (
    compute_feature_vulnerabilities,
    detect_failure_boundary,
)
from model_autopsy.datasets.iris import load_and_validate_iris
from model_autopsy.metrics.evaluator import calculate_metrics
from model_autopsy.models.sklearn_rf import RandomForestAdapter, RandomForestConfig
from model_autopsy.reporting.artifacts import generate_artifacts
from model_autopsy.stress_tests.noise.gaussian import apply_gaussian_noise
from model_autopsy.visualization.curve_plotter import plot_robustness_curve


def run_e001_experiment(
    config_path: Optional[Path] = None,
    seed: int = 42,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute the full E001 experimental pipeline.

    Protocol:
        1. Ingestion & Stratified Split (split_seed=42)
        2. Compute Feature Dispersion (train_std strictly from X_train)
        3. Train Random Forest (model_seed=seed)
        4. Baseline Evaluation (s=0.00)
        5. Systematic Severity Sweep (s in [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
        6. Failure Boundary & Diagnostic Analysis
        7. Artifact Synthesis (CSV, JSON, PNG, manifest, report)

    Args:
        config_path: Path to YAML experiment configuration.
        seed: Execution seed for model and noise RNG.
        output_dir: Destination directory for artifacts.

    Returns:
        Dictionary containing execution summary, metrics, and artifact paths.
    """
    # 1. Load config if provided
    config: Dict[str, Any] = {}
    if config_path is not None and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    exp_cfg = config.get("experiment", {})
    experiment_id = exp_cfg.get("id", "E001")
    protocol_version = exp_cfg.get("protocol_version", "1.0.0")

    dataset_cfg = config.get("dataset", {})
    split_seed = dataset_cfg.get("split", {}).get("split_seed", 42)

    model_cfg = config.get("model", {})
    severities = config.get("stress_test", {}).get(
        "severities", [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
    )
    failure_threshold = float(config.get("evaluation", {}).get("failure_threshold", 0.80))

    if output_dir is None:
        target_out = Path(config.get("artifacts", {}).get("output_dir", "artifacts/experiments/E001"))
    else:
        target_out = Path(output_dir)

    target_out.mkdir(parents=True, exist_ok=True)

    # 2. Ingestion & Stratified Split
    dataset_bundle = load_and_validate_iris(split_seed=split_seed)
    X_train = dataset_bundle.X_train
    y_train = dataset_bundle.y_train
    X_test = dataset_bundle.X_test
    y_test = dataset_bundle.y_test
    train_std = dataset_bundle.train_std

    dataset_metadata = {
        "name": "iris",
        "n_instances": 150,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "feature_names": dataset_bundle.feature_names,
        "target_names": dataset_bundle.target_names,
        "dataset_hash": dataset_bundle.dataset_hash,
        "feature_train_std": [round(float(v), 5) for v in train_std],
        "split_seed": split_seed,
    }

    # 3. Model Training
    rf_config = RandomForestConfig(
        n_estimators=100,
        max_depth=None,
        criterion="gini",
        min_samples_split=2,
        min_samples_leaf=1,
        bootstrap=True,
        random_state=seed,
    )
    model = RandomForestAdapter(config=rf_config)
    model.fit(X_train, y_train)

    model_metadata = {
        "adapter": "RandomForestAdapter",
        "class_name": "RandomForestClassifier",
        "hyperparameters": rf_config.to_dict(),
        "model_seed": seed,
    }

    # 4. Baseline Evaluation (s=0.00)
    baseline_preds = model.predict(X_test)
    baseline_metrics = calculate_metrics(
        y_true=y_test,
        y_pred=baseline_preds,
        baseline_macro_f1=None,  # This establishes the baseline
        failure_threshold=failure_threshold,
    )
    baseline_macro_f1 = baseline_metrics.macro_f1

    # 5. Systematic Severity Sweep
    severity_records: List[Dict[str, Any]] = []
    for sev in severities:
        sev_float = float(sev)
        # Scale-aware Gaussian noise
        pert_res = apply_gaussian_noise(
            X=X_test,
            train_std=train_std,
            severity=sev_float,
            seed=seed,
        )
        preds = model.predict(pert_res.X_corrupted)
        metrics = calculate_metrics(
            y_true=y_test,
            y_pred=preds,
            baseline_macro_f1=baseline_macro_f1,
            failure_threshold=failure_threshold,
        )

        record = {
            "severity": sev_float,
            "macro_f1": metrics.macro_f1,
            "accuracy": metrics.accuracy,
            "absolute_degradation_pp": metrics.absolute_degradation_pp,
            "relative_degradation_pct": metrics.relative_degradation_pct,
            "is_failed": metrics.is_failed,
            "rel_drop_exceeds_15_pct": metrics.rel_drop_exceeds_15_pct,
            "per_class_f1": metrics.per_class_f1,
            "per_class_precision": metrics.per_class_precision,
            "per_class_recall": metrics.per_class_recall,
            "confusion_matrix": metrics.confusion_matrix,
        }
        severity_records.append(record)

    # 6. Failure Boundary & Diagnostic Analysis
    boundary_res = detect_failure_boundary(
        severity_records=severity_records,
        failure_threshold=failure_threshold,
        metric_key="macro_f1",
    )

    feature_vulnerabilities = compute_feature_vulnerabilities(
        model=model,
        X_test=X_test,
        y_test=y_test,
        train_std=train_std,
        feature_names=dataset_bundle.feature_names,
        eval_severity=0.20,
        baseline_macro_f1=baseline_macro_f1,
        seed=seed,
    )

    # 7. Visualization Plot
    plot_path = target_out / "robustness_curve.png"
    plot_robustness_curve(
        severity_records=severity_records,
        output_path=plot_path,
        failure_threshold=failure_threshold,
        experiment_id=experiment_id,
        model_name="RandomForest (Iris)",
        dataset_name="Fisher Iris Dataset",
    )

    # 8. Artifact Serialization
    seeds_config = {
        "split_seed": split_seed,
        "model_seed": seed,
        "noise_seed": seed,
        "planned_research_seeds": [42, 123, 456, 789, 1011],
    }

    artifacts = generate_artifacts(
        experiment_id=experiment_id,
        output_dir=target_out,
        dataset_metadata=dataset_metadata,
        model_metadata=model_metadata,
        seeds_config=seeds_config,
        severity_records=severity_records,
        failure_boundary_result=boundary_res.to_dict(),
        feature_vulnerabilities=feature_vulnerabilities,
        baseline_metrics=baseline_metrics.to_dict(),
        protocol_version=protocol_version,
        failure_threshold=failure_threshold,
    )
    artifacts["robustness_curve.png"] = plot_path

    return {
        "status": "success",
        "experiment_id": experiment_id,
        "seeds": seeds_config,
        "baseline_macro_f1": baseline_macro_f1,
        "baseline_accuracy": baseline_metrics.accuracy,
        "failure_boundary": boundary_res.to_dict(),
        "severity_records": severity_records,
        "feature_vulnerabilities": feature_vulnerabilities,
        "artifacts": {k: str(v) for k, v in artifacts.items()},
    }
