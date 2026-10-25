"""E002 multi-corruption comparative experiment execution orchestrator."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from model_autopsy.analysis.statistical import aggregate_multi_seed_results
from model_autopsy.datasets.iris import load_and_validate_iris
from model_autopsy.metrics.evaluator import calculate_metrics
from model_autopsy.models.sklearn_rf import RandomForestAdapter, RandomForestConfig
from model_autopsy.reporting.artifacts import generate_e002_artifacts
from model_autopsy.stress_tests.missingness.mcar import apply_feature_missingness_mcar
from model_autopsy.stress_tests.noise.gaussian import apply_gaussian_noise
from model_autopsy.stress_tests.outliers.impulsive import apply_feature_outliers
from model_autopsy.visualization.curve_plotter import plot_e002_multicorruption_comparison


def run_e002_experiment(
    config_path: Optional[Path] = None,
    seeds: Optional[List[int]] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute the full E002 cross-corruption comparative experiment.

    Protocol:
        1. Ingest and freeze canonical Stratified 80/20 train/test split (split_seed=42).
        2. Compute training feature dispersion (train_std) and feature means (train_mean)
           exclusively on X_train.
        3. Evaluate across 5 independent seeds: [42, 123, 456, 789, 1011].
        4. For each seed, train RandomForestClassifier(100 estimators, unconstrained depth).
        5. For each corruption modality (Gaussian noise, MCAR missingness, Impulsive outliers):
           - Sweep all 7 severity levels: [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30].
           - Record exact evaluation metrics, relative and absolute degradation.
        6. Compute multi-seed statistical aggregations (means, sample std with ddof=1,
           SEM, 95% Student's t CI with df=4, failure counts, failure boundaries).
        7. Generate publication-quality comparison curve, aggregate CSV/JSON tables,
           reproducibility manifest, and formal research report.

    Args:
        config_path: Path to YAML experiment configuration.
        seeds: List of random seeds (default: [42, 123, 456, 789, 1011]).
        output_dir: Destination directory for artifacts (default: artifacts/experiments/E002).

    Returns:
        Dictionary containing execution summary, metrics, and artifact paths.
    """
    # 1. Load config if provided
    config: Dict[str, Any] = {}
    if config_path is not None and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    exp_cfg = config.get("experiment", {})
    experiment_id = exp_cfg.get("id", "E002")
    protocol_version = exp_cfg.get("protocol_version", "1.0.0")

    dataset_cfg = config.get("dataset", {})
    split_seed = dataset_cfg.get("split", {}).get("split_seed", 42)

    model_cfg = config.get("model", {})
    configured_seeds = model_cfg.get("research_seeds", [42, 123, 456, 789, 1011])
    active_seeds = seeds if seeds is not None else configured_seeds

    stress_cfg = config.get("stress_tests", {})
    severities = stress_cfg.get("severities", [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])

    eval_cfg = config.get("evaluation", {})
    failure_threshold = float(eval_cfg.get("failure_threshold", 0.80))

    if output_dir is not None:
        target_out = Path(output_dir)
    else:
        target_out = Path(config.get("artifacts", {}).get("output_dir", "artifacts/experiments/E002"))
    target_out.mkdir(parents=True, exist_ok=True)

    # 2. Frozen Dataset Ingestion & Partitioning
    bundle = load_and_validate_iris(split_seed=split_seed)
    train_mean = bundle.train_mean if bundle.train_mean is not None else bundle.X_train.mean(axis=0)

    dataset_metadata = {
        "name": "iris",
        "n_total": 150,
        "n_train": len(bundle.X_train),
        "n_test": len(bundle.X_test),
        "feature_names": bundle.feature_names,
        "target_names": bundle.target_names,
        "feature_sigmas": [round(float(v), 6) for v in bundle.train_std],
        "feature_means": [round(float(v), 6) for v in train_mean],
        "dataset_hash": bundle.dataset_hash,
        "split_seed": split_seed,
    }

    model_metadata = {
        "family": "RandomForestClassifier",
        "n_estimators": 100,
        "max_depth": None,
        "criterion": "gini",
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "bootstrap": True,
    }

    seeds_config = {
        "split_seed": split_seed,
        "research_seeds": active_seeds,
    }

    corruption_operators = {
        "gaussian_noise": {
            "label": "Additive Gaussian Noise",
            "fn": lambda X, s, seed: apply_gaussian_noise(X, bundle.train_std, s, seed=seed),
        },
        "feature_missingness_mcar": {
            "label": "MCAR Missingness (Mean Imputed)",
            "fn": lambda X, s, seed: apply_feature_missingness_mcar(X, train_mean, s, seed=seed),
        },
        "feature_outliers": {
            "label": "Impulsive Outliers (5σ)",
            "fn": lambda X, s, seed: apply_feature_outliers(X, train_mean, bundle.train_std, s, displacement_factor=5.0, seed=seed),
        },
    }

    corruption_results: Dict[str, Any] = {}

    # 3. Execution Sweep across Corruption Types and Seeds
    for corr_id, corr_spec in corruption_operators.items():
        per_seed_runs: Dict[int, Dict[str, Any]] = {}

        for seed in active_seeds:
            # Fit model on training partition strictly
            rf_config = RandomForestConfig(
                n_estimators=100,
                max_depth=None,
                criterion="gini",
                min_samples_split=2,
                min_samples_leaf=1,
                bootstrap=True,
                random_state=seed,
            )
            rf_adapter = RandomForestAdapter(rf_config)
            rf_adapter.fit(bundle.X_train, bundle.y_train)

            # Clean baseline evaluation (s=0.00)
            baseline_preds = rf_adapter.predict(bundle.X_test)
            baseline_metrics = calculate_metrics(
                y_true=bundle.y_test,
                y_pred=baseline_preds,
                baseline_macro_f1=None,
                failure_threshold=failure_threshold,
            )
            ref_baseline_macro_f1 = baseline_metrics.macro_f1

            severity_records = []
            for s in severities:
                # Apply corruption to evaluation partition
                pert_res = corr_spec["fn"](bundle.X_test, s, seed)
                preds = rf_adapter.predict(pert_res.X_corrupted)
                metrics = calculate_metrics(
                    y_true=bundle.y_test,
                    y_pred=preds,
                    baseline_macro_f1=ref_baseline_macro_f1,
                    failure_threshold=failure_threshold,
                )

                rec = {
                    "severity": float(s),
                    "macro_f1": metrics.macro_f1,
                    "accuracy": metrics.accuracy,
                    "per_class_f1": metrics.per_class_f1,
                    "per_class_precision": metrics.per_class_precision,
                    "per_class_recall": metrics.per_class_recall,
                    "confusion_matrix": metrics.confusion_matrix,
                    "absolute_degradation_pp": metrics.absolute_degradation_pp,
                    "relative_degradation_pct": metrics.relative_degradation_pct,
                    "is_failed": metrics.is_failed,
                    "rel_drop_exceeds_15_pct": metrics.rel_drop_exceeds_15_pct,
                }
                severity_records.append(rec)

            # Compute observed boundary for this seed
            observed_boundary = None
            for rec in severity_records:
                if rec["macro_f1"] < failure_threshold:
                    observed_boundary = rec["severity"]
                    break

            per_seed_runs[seed] = {
                "seed": seed,
                "baseline_macro_f1": ref_baseline_macro_f1,
                "baseline_accuracy": baseline_metrics.accuracy,
                "severity_records": severity_records,
                "failure_boundary": {
                    "observed_boundary": observed_boundary,
                    "threshold": failure_threshold,
                },
            }

        # Multi-seed statistical aggregation for this corruption modality
        agg_eval_result = aggregate_multi_seed_results(
            per_seed_runs=per_seed_runs,
            severities=severities,
            failure_threshold=failure_threshold,
        )
        corruption_results[corr_id] = agg_eval_result

    # 4. Multi-Corruption Comparative Robustness Curve
    plot_dict = {
        corr_spec["label"]: [
            {
                "severity": agg.severity,
                "macro_f1_mean": agg.macro_f1.mean,
                "macro_f1_ci_lower": agg.macro_f1.ci_lower,
                "macro_f1_ci_upper": agg.macro_f1.ci_upper,
            }
            for agg in corruption_results[corr_id].severity_aggregates
        ]
        for corr_id, corr_spec in corruption_operators.items()
    }
    plot_path = target_out / "robustness_comparison.png"
    plot_e002_multicorruption_comparison(
        corruption_aggregates=plot_dict,
        output_path=plot_path,
        failure_threshold=failure_threshold,
        experiment_id=experiment_id,
        model_name="Random Forest Classifier",
        dataset_name="Iris Flower Dataset",
    )

    # 5. Serialize Artifacts, Manifest, and Report
    artifacts = generate_e002_artifacts(
        experiment_id=experiment_id,
        output_dir=target_out,
        dataset_metadata=dataset_metadata,
        model_metadata=model_metadata,
        seeds_config=seeds_config,
        corruption_results=corruption_results,
        protocol_version=protocol_version,
        failure_threshold=failure_threshold,
    )
    artifacts["robustness_comparison.png"] = plot_path

    return {
        "status": "success",
        "experiment_id": experiment_id,
        "seeds": active_seeds,
        "corruptions_evaluated": list(corruption_operators.keys()),
        "corruption_results": {k: v.to_dict() for k, v in corruption_results.items()},
        "artifacts": {k: str(v) for k, v in artifacts.items()},
    }
