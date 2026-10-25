"""E003 cross-model comparative robustness experiment execution orchestrator."""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import yaml

from model_autopsy.analysis.statistical import aggregate_multi_seed_results
from model_autopsy.datasets.iris import load_and_validate_iris
from model_autopsy.metrics.evaluator import calculate_metrics
from model_autopsy.models.sklearn_gb import GradientBoostingAdapter, GradientBoostingConfig
from model_autopsy.models.sklearn_logistic import LogisticRegressionAdapter, LogisticRegressionConfig
from model_autopsy.models.sklearn_rf import RandomForestAdapter, RandomForestConfig
from model_autopsy.reporting.artifacts import generate_e003_artifacts
from model_autopsy.stress_tests.missingness.mcar import apply_feature_missingness_mcar
from model_autopsy.stress_tests.noise.gaussian import apply_gaussian_noise
from model_autopsy.stress_tests.outliers.impulsive import apply_feature_outliers
from model_autopsy.visualization.curve_plotter import plot_e003_cross_model_comparison


def run_e003_experiment(
    config_path: Optional[Path] = None,
    seeds: Optional[List[int]] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute the full E003 cross-model comparative robustness experiment.

    Protocol:
        1. Ingest and freeze canonical Stratified 80/20 train/test split (split_seed=42).
        2. Compute training feature dispersion (train_std, ddof=1) and means (train_mean)
           exclusively on X_train.
        3. Evaluate 3 distinct architectures:
           - Random Forest (Bagged orthogonal trees)
           - Logistic Regression (Pipeline with training-fitted StandardScaler)
           - Gradient Boosting (Additive sequential trees)
        4. Evaluate across 5 independent seeds: [42, 123, 456, 789, 1011].
        5. For each model and seed, fit strictly on X_train, y_train.
        6. For each corruption modality (Gaussian noise, MCAR missingness, Impulsive outliers):
           - Sweep all 7 severity levels: [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30].
           - Record exact evaluation metrics, absolute and relative degradation.
        7. Compute multi-seed statistical aggregations (means, sample std with ddof=1,
           SEM, 95% Student's t CI with df=4, failure counts, failure boundaries).
        8. Generate publication-quality 3-panel comparison curves, aggregate CSV/JSON tables,
           reproducibility manifest, and formal research report.

    Args:
        config_path: Path to YAML experiment configuration.
        seeds: List of random seeds (default: [42, 123, 456, 789, 1011]).
        output_dir: Destination directory for artifacts (default: artifacts/experiments/E003).

    Returns:
        Dictionary containing execution summary, metrics, and artifact paths.
    """
    # 1. Load config if provided
    config: Dict[str, Any] = {}
    if config_path is not None and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    exp_cfg = config.get("experiment", {})
    experiment_id = exp_cfg.get("id", "E003")
    protocol_version = exp_cfg.get("protocol_version", "1.0.0")

    dataset_cfg = config.get("dataset", {})
    split_seed = dataset_cfg.get("split", {}).get("split_seed", 42)

    seeds_cfg = config.get("seeds", {})
    configured_seeds = seeds_cfg.get("research_seeds", [42, 123, 456, 789, 1011])
    active_seeds = seeds if seeds is not None else configured_seeds

    stress_cfg = config.get("stress_tests", {})
    severities = stress_cfg.get("severities", [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])

    eval_cfg = config.get("evaluation", {})
    failure_threshold = float(eval_cfg.get("failure_threshold", 0.80))

    if output_dir is not None:
        target_out = Path(output_dir)
    else:
        target_out = Path(config.get("artifacts", {}).get("output_dir", "artifacts/experiments/E003"))
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

    seeds_config = {
        "split_seed": split_seed,
        "research_seeds": active_seeds,
    }

    # 3. Model Factories & Metadata
    model_definitions: Dict[str, Dict[str, Any]] = {
        "random_forest": {
            "label": "Random Forest",
            "family": "ensemble",
            "factory": lambda s: RandomForestAdapter(
                RandomForestConfig(
                    n_estimators=100,
                    max_depth=None,
                    criterion="gini",
                    min_samples_split=2,
                    min_samples_leaf=1,
                    bootstrap=True,
                    random_state=s,
                )
            ),
            "metadata": {
                "family": "RandomForestClassifier",
                "n_estimators": 100,
                "max_depth": None,
                "criterion": "gini",
                "min_samples_split": 2,
                "min_samples_leaf": 1,
                "bootstrap": True,
                "preprocessing": "none",
            },
        },
        "logistic_regression": {
            "label": "Logistic Regression (Scaled)",
            "family": "linear",
            "factory": lambda s: LogisticRegressionAdapter(
                LogisticRegressionConfig(
                    penalty="l2",
                    C=1.0,
                    solver="lbfgs",
                    max_iter=1000,
                    random_state=s,
                    with_mean=True,
                    with_std=True,
                )
            ),
            "metadata": {
                "family": "LogisticRegression",
                "penalty": "l2",
                "C": 1.0,
                "solver": "lbfgs",
                "max_iter": 1000,
                "preprocessing": "Pipeline(StandardScaler(with_mean=True, with_std=True))",
                "scaling_source": "train_only",
            },
        },
        "gradient_boosting": {
            "label": "Gradient Boosting",
            "family": "boosting",
            "factory": lambda s: GradientBoostingAdapter(
                GradientBoostingConfig(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=3,
                    subsample=1.0,
                    criterion="friedman_mse",
                    random_state=s,
                )
            ),
            "metadata": {
                "family": "GradientBoostingClassifier",
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 3,
                "subsample": 1.0,
                "criterion": "friedman_mse",
                "preprocessing": "none",
            },
        },
    }

    # 4. Corruption Operators
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
            "fn": lambda X, s, seed: apply_feature_outliers(
                X, train_mean, bundle.train_std, s, displacement_factor=5.0, seed=seed
            ),
        },
    }

    results_by_model: Dict[str, Dict[str, Any]] = {}
    models_metadata: Dict[str, Any] = {}

    # 5. Nested Evaluation: Model -> Corruption -> Seed -> Severity
    for model_id, model_spec in model_definitions.items():
        models_metadata[model_id] = model_spec["metadata"]
        results_by_model[model_id] = {}

        for corr_id, corr_spec in corruption_operators.items():
            per_seed_runs: Dict[int, Dict[str, Any]] = {}

            for seed in active_seeds:
                # Instantiate and fit model on training partition strictly
                adapter = model_spec["factory"](seed)
                adapter.fit(bundle.X_train, bundle.y_train)

                # Baseline evaluation on clean test partition (s=0.00)
                clean_preds = adapter.predict(bundle.X_test)
                clean_metrics = calculate_metrics(
                    y_true=bundle.y_test,
                    y_pred=clean_preds,
                    baseline_macro_f1=None,
                    failure_threshold=failure_threshold,
                )
                ref_baseline_macro_f1 = clean_metrics.macro_f1

                severity_records = []
                for s in severities:
                    # Apply corruption to test partition
                    pert_res = corr_spec["fn"](bundle.X_test, s, seed)
                    preds = adapter.predict(pert_res.X_corrupted)
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

                # Compute observed failure boundary for this seed
                observed_boundary = None
                for rec in severity_records:
                    if rec["macro_f1"] < failure_threshold:
                        observed_boundary = rec["severity"]
                        break

                per_seed_runs[seed] = {
                    "seed": seed,
                    "baseline_macro_f1": ref_baseline_macro_f1,
                    "baseline_accuracy": clean_metrics.accuracy,
                    "severity_records": severity_records,
                    "failure_boundary": {
                        "observed_boundary": observed_boundary,
                        "threshold": failure_threshold,
                    },
                }

            # Statistical aggregation across seeds
            agg_eval_result = aggregate_multi_seed_results(
                per_seed_runs=per_seed_runs,
                severities=severities,
                failure_threshold=failure_threshold,
            )
            results_by_model[model_id][corr_id] = agg_eval_result

    # 6. Generate 3-Panel Comparison Figure
    plot_path = target_out / "robustness_comparison.png"
    plot_e003_cross_model_comparison(
        results_by_model=results_by_model,
        output_path=plot_path,
        failure_threshold=failure_threshold,
        dataset_name="Iris Flower Dataset",
        experiment_id=experiment_id,
    )

    # 7. Generate Machine-Readable Artifacts, Manifest, and Research Report
    artifacts = generate_e003_artifacts(
        experiment_id=experiment_id,
        output_dir=target_out,
        dataset_metadata=dataset_metadata,
        models_metadata=models_metadata,
        seeds_config=seeds_config,
        results_by_model=results_by_model,
        protocol_version=protocol_version,
        failure_threshold=failure_threshold,
    )
    artifacts["robustness_comparison.png"] = plot_path

    return {
        "experiment_id": experiment_id,
        "protocol_version": protocol_version,
        "dataset": dataset_metadata,
        "models": models_metadata,
        "seeds": active_seeds,
        "severities": severities,
        "results_by_model": results_by_model,
        "artifacts": {k: str(v) for k, v in artifacts.items()},
        "output_dir": str(target_out),
    }
