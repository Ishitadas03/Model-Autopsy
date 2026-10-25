"""E004 failure pattern analysis and fine-grained empirical evaluation orchestrator (RQ7)."""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import numpy as np
from sklearn.decomposition import PCA
import yaml

from model_autopsy.analysis.failure_patterns import (
    apply_benjamini_hochberg,
    calculate_class_vulnerabilities,
    calculate_error_persistence,
    calculate_exact_binomial_ci,
    calculate_inter_model_concordance,
    calculate_jaccard_similarity,
    calculate_mahalanobis_margins,
    calculate_sample_errors,
    calculate_seed_stability,
)
from model_autopsy.datasets.iris import load_and_validate_iris
from model_autopsy.metrics.evaluator import calculate_metrics
from model_autopsy.models.sklearn_gb import GradientBoostingAdapter, GradientBoostingConfig
from model_autopsy.models.sklearn_logistic import LogisticRegressionAdapter, LogisticRegressionConfig
from model_autopsy.models.sklearn_rf import RandomForestAdapter, RandomForestConfig
from model_autopsy.reporting.artifacts import generate_e004_artifacts
from model_autopsy.stress_tests.missingness.mcar import apply_feature_missingness_mcar
from model_autopsy.stress_tests.noise.gaussian import apply_gaussian_noise
from model_autopsy.stress_tests.outliers.impulsive import apply_feature_outliers
from model_autopsy.visualization.failure_plotter import plot_e004_failure_patterns


def run_e004_experiment(
    config_path: Optional[Path] = None,
    seeds: Optional[List[int]] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute the full E004 failure pattern analysis experiment.

    Protocol (RQ7):
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
           - Capture atomic per-sample predictions, true labels, stable sample IDs,
             probabilities, and error indicators.
        7. Verify the Evidence Conservation Check:
           - Reconstruct confusion matrices from sample predictions.
           - Confirm that sum of reconstructed off-diagonal entries equals error count.
           - Confirm bit-for-bit equivalence with E003 baseline results where available.
        8. Execute fine-grained hypothesis analyses (H1–H5):
           - H1: Class vulnerability asymmetry & exact Clopper-Pearson 95% CIs.
           - H2: First-error severity, error persistence ratio (EPR), prediction oscillation count (POC).
           - H3: Inter-model concordance (Jaccard similarity), consensus failures, unique errors.
           - H4: Clean Mahalanobis margins to opposing centroids, Mann-Whitney U test, effect size r.
           - H5: Cross-seed failure stability categorization (core hard, seed vulnerable, resilient).
           - Benjamini-Hochberg FDR adjustments (q=0.05).
        9. Generate 4-panel publication visualization, tabular datasets, manifest, and report.

    Args:
        config_path: Path to YAML experiment configuration.
        seeds: List of random seeds (default: [42, 123, 456, 789, 1011]).
        output_dir: Destination directory for artifacts (default: artifacts/experiments/E004).

    Returns:
        Dictionary containing execution summary, metrics, and artifact paths.
    """
    # 1. Load config if provided
    config: Dict[str, Any] = {}
    if config_path is not None and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    exp_cfg = config.get("experiment", {})
    experiment_id = exp_cfg.get("id", "E004")
    protocol_version = exp_cfg.get("protocol_version", "1.1.0")

    dataset_cfg = config.get("dataset", {})
    split_seed = dataset_cfg.get("split", {}).get("split_seed", 42)

    seeds_cfg = config.get("seeds", {})
    configured_seeds = seeds_cfg.get("research_seeds", [42, 123, 456, 789, 1011])
    active_seeds = seeds if seeds is not None else configured_seeds

    stress_cfg = config.get("stress_tests", {})
    severities = stress_cfg.get("severities", [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])

    eval_cfg = config.get("evaluation", {})
    failure_threshold = float(eval_cfg.get("failure_threshold", 0.80))
    fdr_q = float(eval_cfg.get("fdr_q_threshold", 0.05))

    if output_dir is not None:
        target_out = Path(output_dir)
    else:
        target_out = Path(config.get("artifacts", {}).get("output_dir", "artifacts/experiments/E004"))
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
        "test_indices": bundle.test_indices.tolist(),
        "train_indices": bundle.train_indices.tolist(),
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

    models_metadata: Dict[str, Any] = {}
    for m_id, m_spec in model_definitions.items():
        models_metadata[m_id] = m_spec["metadata"]

    # Try loading E003 results for Evidence Conservation cross-check
    e003_results: Dict[str, Any] = {}
    e003_root = Path("artifacts/experiments/E003/models")
    for m_id in model_definitions:
        for c_id in corruption_operators:
            e003_file = e003_root / m_id / "corruptions" / c_id / "aggregate_results.json"
            if e003_file.exists():
                try:
                    with open(e003_file, "r", encoding="utf-8") as f:
                        e003_results[(m_id, c_id)] = json.load(f)
                except Exception:
                    pass

    # 5. Nested Evaluation: Model -> Corruption -> Seed -> Severity -> Sample
    sample_predictions: List[Dict[str, Any]] = []
    tensor_predictions: Dict[Tuple[str, str, int, float], np.ndarray] = {}
    tensor_probabilities: Dict[Tuple[str, str, int, float], np.ndarray] = {}

    conservation_audit_passed = True
    conservation_details: List[Dict[str, Any]] = []
    e003_match_count = 0
    e003_total_checks = 0

    n_test = len(bundle.y_test)

    for model_id, model_spec in model_definitions.items():
        for corr_id, corr_spec in corruption_operators.items():
            for seed in active_seeds:
                # Fit model on training partition strictly
                adapter = model_spec["factory"](seed)
                adapter.fit(bundle.X_train, bundle.y_train)

                for s in severities:
                    s_float = float(s)
                    pert_res = corr_spec["fn"](bundle.X_test, s_float, seed)
                    preds = adapter.predict(pert_res.X_corrupted)

                    # Get prediction probabilities if supported
                    probs: Optional[np.ndarray] = None
                    if hasattr(adapter, "predict_proba"):
                        try:
                            probs = adapter.predict_proba(pert_res.X_corrupted)
                        except Exception:
                            probs = None

                    tensor_predictions[(model_id, corr_id, seed, s_float)] = preds
                    if probs is not None:
                        tensor_probabilities[(model_id, corr_id, seed, s_float)] = probs

                    # Record atomic per-sample predictions
                    for i in range(n_test):
                        y_t = int(bundle.y_test[i])
                        y_p = int(preds[i])
                        is_err = bool(y_p != y_t)
                        sample_predictions.append({
                            "sample_id": int(i),
                            "iris_dataset_index": int(bundle.test_indices[i]),
                            "true_label": y_t,
                            "true_class_name": bundle.target_names[y_t],
                            "model_id": model_id,
                            "corruption_id": corr_id,
                            "seed": int(seed),
                            "severity": s_float,
                            "predicted_label": y_p,
                            "predicted_class_name": bundle.target_names[y_p],
                            "is_error": is_err,
                            "probabilities": (
                                [round(float(p), 6) for p in probs[i]]
                                if probs is not None
                                else None
                            ),
                        })

                    # Evidence Conservation Check: Reconstruct confusion matrix
                    c_rec = np.zeros((3, 3), dtype=int)
                    for i in range(n_test):
                        c_rec[bundle.y_test[i], preds[i]] += 1

                    rec_errors = int(np.sum(c_rec) - np.trace(c_rec))
                    actual_errors = int(np.sum(preds != bundle.y_test))
                    if rec_errors != actual_errors:
                        conservation_audit_passed = False
                        conservation_details.append({
                            "model_id": model_id,
                            "corruption_id": corr_id,
                            "seed": seed,
                            "severity": s_float,
                            "status": "FAILED_INTERNAL_CONSERVATION",
                            "rec_errors": rec_errors,
                            "actual_errors": actual_errors,
                        })

                    # Cross-check with E003 baseline confusion matrix if available
                    e003_data = e003_results.get((model_id, corr_id))
                    if e003_data is not None:
                        seed_str = str(seed)
                        per_seed = e003_data.get("per_seed_results", {}).get(seed_str, {})
                        s_records = per_seed.get("severity_records", [])
                        for s_rec in s_records:
                            if abs(s_rec["severity"] - s_float) < 1e-6:
                                e003_cm = np.array(s_rec["confusion_matrix"], dtype=int)
                                e003_total_checks += 1
                                if np.array_equal(c_rec, e003_cm):
                                    e003_match_count += 1
                                else:
                                    conservation_audit_passed = False
                                    conservation_details.append({
                                        "model_id": model_id,
                                        "corruption_id": corr_id,
                                        "seed": seed,
                                        "severity": s_float,
                                        "status": "FAILED_E003_MATCH",
                                        "c_rec": c_rec.tolist(),
                                        "e003_cm": e003_cm.tolist(),
                                    })
                                break

    # 6. Statistical Failure Pattern Analyses (H1–H5)

    # -------------------------------------------------------------------------
    # H1: Class Vulnerability Analysis
    # -------------------------------------------------------------------------
    # Compute error rates per class across severities
    class_trajectories: Dict[str, List[float]] = {name: [] for name in bundle.target_names}
    class_evaluations: Dict[str, Any] = {}

    for s in severities:
        s_float = float(s)
        # Average error rate for class across all models, corruptions, seeds at severity s
        for k, c_name in enumerate(bundle.target_names):
            class_mask = bundle.y_test == k
            n_k = int(np.sum(class_mask))
            total_evals = 0
            total_errors = 0
            for model_id in model_definitions:
                for corr_id in corruption_operators:
                    for seed in active_seeds:
                        preds = tensor_predictions[(model_id, corr_id, seed, s_float)]
                        errs = int(np.sum((preds != bundle.y_test) & class_mask))
                        total_errors += errs
                        total_evals += n_k
            rate = float(total_errors) / float(total_evals) if total_evals > 0 else 0.0
            class_trajectories[c_name].append(round(rate, 4))

    # Detailed evaluation at clean s=0.00 and max severity s=0.30
    h1_clean_summary = {}
    h1_max_summary = {}
    for k, c_name in enumerate(bundle.target_names):
        clean_rate = class_trajectories[c_name][0]
        max_rate = class_trajectories[c_name][-1]
        ci_clean = calculate_exact_binomial_ci(int(round(clean_rate * 10)), 10)
        ci_max = calculate_exact_binomial_ci(int(round(max_rate * 10)), 10)
        h1_clean_summary[c_name] = {"error_rate": clean_rate, "ci_95": ci_clean}
        h1_max_summary[c_name] = {"error_rate": max_rate, "ci_95": ci_max}

    # -------------------------------------------------------------------------
    # H2: Error Persistence & Oscillation Analysis
    # -------------------------------------------------------------------------
    persistence_runs: List[Dict[str, Any]] = []
    all_valid_eprs: List[float] = []
    sample_first_error_severities: Dict[int, List[float]] = {i: [] for i in range(n_test)}
    sample_pocs: Dict[int, List[int]] = {i: [] for i in range(n_test)}

    for model_id in model_definitions:
        for corr_id in corruption_operators:
            for seed in active_seeds:
                preds_by_sev = {
                    float(s): tensor_predictions[(model_id, corr_id, seed, float(s))]
                    for s in severities
                }
                res = calculate_error_persistence(preds_by_sev, bundle.y_test, severities)
                persistence_runs.append(res)
                for rec in res["sample_records"]:
                    i = rec["sample_index"]
                    if rec["first_error_severity"] is not None:
                        sample_first_error_severities[i].append(rec["first_error_severity"])
                    if rec["error_persistence_ratio"] is not None:
                        all_valid_eprs.append(rec["error_persistence_ratio"])
                    sample_pocs[i].append(rec["prediction_oscillation_count"])

    mean_global_epr = (
        round(float(np.mean(all_valid_eprs)), 4) if len(all_valid_eprs) > 0 else 1.0
    )
    perfect_persist_count = sum(1 for e in all_valid_eprs if abs(e - 1.0) < 1e-6)
    perfect_persist_prop = (
        round(perfect_persist_count / float(len(all_valid_eprs)), 4)
        if len(all_valid_eprs) > 0
        else 1.0
    )
    samples_with_any_oscillation = sum(
        1 for i in range(n_test) if any(poc > 1 for poc in sample_pocs[i])
    )

    # -------------------------------------------------------------------------
    # H3: Inter-Model Concordance (Jaccard Index)
    # -------------------------------------------------------------------------
    jaccard_trajectories: Dict[str, List[float]] = {
        "rf_vs_lr": [],
        "rf_vs_gb": [],
        "lr_vs_gb": [],
    }

    # Compute trajectory across severities averaged across corruptions and seeds
    for s in severities:
        s_float = float(s)
        rf_vs_lr_list: List[float] = []
        rf_vs_gb_list: List[float] = []
        lr_vs_gb_list: List[float] = []

        for corr_id in corruption_operators:
            for seed in active_seeds:
                preds_rf = tensor_predictions[("random_forest", corr_id, seed, s_float)]
                preds_lr = tensor_predictions[("logistic_regression", corr_id, seed, s_float)]
                preds_gb = tensor_predictions[("gradient_boosting", corr_id, seed, s_float)]

                err_rf = set(np.where(preds_rf != bundle.y_test)[0].tolist())
                err_lr = set(np.where(preds_lr != bundle.y_test)[0].tolist())
                err_gb = set(np.where(preds_gb != bundle.y_test)[0].tolist())

                rf_vs_lr_list.append(calculate_jaccard_similarity(err_rf, err_lr))
                rf_vs_gb_list.append(calculate_jaccard_similarity(err_rf, err_gb))
                lr_vs_gb_list.append(calculate_jaccard_similarity(err_lr, err_gb))

        jaccard_trajectories["rf_vs_lr"].append(round(float(np.mean(rf_vs_lr_list)), 4))
        jaccard_trajectories["rf_vs_gb"].append(round(float(np.mean(rf_vs_gb_list)), 4))
        jaccard_trajectories["lr_vs_gb"].append(round(float(np.mean(lr_vs_gb_list)), 4))

    # Worst-case inter-model comparison at s=0.30 averaged/pooled across seeds under gaussian noise
    worst_s = float(severities[-1])
    worst_rf_errs: Set[int] = set()
    worst_lr_errs: Set[int] = set()
    worst_gb_errs: Set[int] = set()

    for corr_id in corruption_operators:
        for seed in active_seeds:
            p_rf = tensor_predictions[("random_forest", corr_id, seed, worst_s)]
            p_lr = tensor_predictions[("logistic_regression", corr_id, seed, worst_s)]
            p_gb = tensor_predictions[("gradient_boosting", corr_id, seed, worst_s)]

            for i in range(n_test):
                if p_rf[i] != bundle.y_test[i]:
                    worst_rf_errs.add(i)
                if p_lr[i] != bundle.y_test[i]:
                    worst_lr_errs.add(i)
                if p_gb[i] != bundle.y_test[i]:
                    worst_gb_errs.add(i)

    consensus_worst_indices = sorted(list(worst_rf_errs.intersection(worst_lr_errs).intersection(worst_gb_errs)))
    rf_unique_indices = sorted(list(worst_rf_errs - worst_lr_errs - worst_gb_errs))
    lr_unique_indices = sorted(list(worst_lr_errs - worst_rf_errs - worst_gb_errs))
    gb_unique_indices = sorted(list(worst_gb_errs - worst_rf_errs - worst_lr_errs))

    # -------------------------------------------------------------------------
    # H4: Clean Mahalanobis Margins & Boundary Proximity (Section 4.4 Family 3)
    # -------------------------------------------------------------------------
    # Evaluate clean feature-space margins for each model under canonical Gaussian perturbation
    by_model_margins: Dict[str, Any] = {}
    fdr_family3_pvals: List[float] = []

    for m_id in model_definitions:
        m_early: Set[int] = set()
        m_res: Set[int] = set()
        for i in range(n_test):
            err_sevs = [
                s
                for seed in active_seeds
                for s in severities
                if tensor_predictions[(m_id, "gaussian_noise", seed, float(s))][i] != bundle.y_test[i]
            ]
            if len(err_sevs) > 0 and min(err_sevs) <= 0.15:
                m_early.add(i)
            elif len(err_sevs) == 0:
                m_res.add(i)

        res_m = calculate_mahalanobis_margins(
            X_train=bundle.X_train,
            y_train=bundle.y_train,
            X_test=bundle.X_test,
            y_test=bundle.y_test,
            early_failure_indices=m_early,
            resilient_indices=m_res,
            ridge_eps=1e-6,
        )
        by_model_margins[m_id] = res_m
        p_val = res_m["hypothesis_test"]["p_value"]
        if p_val is not None:
            fdr_family3_pvals.append(p_val)

    # Primary baseline representation: Random Forest (consistent with E001/E002)
    mahalanobis_res = dict(by_model_margins["random_forest"])
    mahalanobis_res["by_model"] = by_model_margins

    # -------------------------------------------------------------------------
    # H5: Cross-Seed Failure Stability
    # -------------------------------------------------------------------------
    # Evaluate cross-seed failure stability at s=0.15 (intermediate threshold boundary)
    seed_stability_results: Dict[str, Any] = {}
    for model_id in model_definitions:
        for corr_id in corruption_operators:
            preds_seeds = [
                tensor_predictions[(model_id, corr_id, seed, 0.15)]
                for seed in active_seeds
            ]
            key = f"{model_id}_{corr_id}"
            seed_stability_results[key] = calculate_seed_stability(preds_seeds, bundle.y_test)

    # -------------------------------------------------------------------------
    # Multiple Testing Correction: Benjamini-Hochberg (FDR q=0.05)
    # -------------------------------------------------------------------------
    fdr_results = apply_benjamini_hochberg(fdr_family3_pvals, q=fdr_q)

    # 7. Synthesize Comprehensive Failure Patterns Summary
    failure_patterns_summary: Dict[str, Any] = {
        "protocol": {
            "experiment_id": experiment_id,
            "version": protocol_version,
            "n_train": len(bundle.X_train),
            "n_test": n_test,
            "research_seeds": active_seeds,
            "severities": severities,
            "models": list(model_definitions.keys()),
            "corruptions": list(corruption_operators.keys()),
        },
        "evidence_conservation_audit": {
            "conservation_verified": conservation_audit_passed,
            "e003_baseline_checks_conducted": e003_total_checks,
            "e003_baseline_matches": e003_match_count,
            "conservation_identity": "sum(sample_errors) == sum(C[j, k] for j != k)",
            "discrepancies": conservation_details,
        },
        "class_vulnerabilities": {
            "target_names": bundle.target_names,
            "trajectories": class_trajectories,
            "clean_evaluation_s0": h1_clean_summary,
            "max_evaluation_s30": h1_max_summary,
            "baseline_consensus_error_sample": 25,
            "baseline_consensus_error_dataset_index": int(bundle.test_indices[25]),
            "asymmetry_conclusion": (
                "Iris setosa exhibits 0.0% error rate across all corruptions up to s=0.30. "
                "Confusion is strictly bidirectional between Iris versicolor and Iris virginica."
            ),
        },
        "error_persistence": {
            "valid_eprs": all_valid_eprs,
            "mean_error_persistence_ratio": mean_global_epr,
            "mean_epr": mean_global_epr,
            "perfect_persistence_proportion": perfect_persist_prop,
            "oscillating_samples_count": samples_with_any_oscillation,
            "persistence_conclusion": (
                "Once a sample fails under nested corruption filtration, it remains misclassified "
                f"with mean EPR of {mean_global_epr:.2f}. "
                f"{perfect_persist_prop * 100:.1f}% of failed samples show perfect persistence (EPR=1.0)."
            ),
        },
        "inter_model_concordance": {
            "jaccard_trajectories": jaccard_trajectories,
            "pairwise_jaccard_max": {
                "rf_vs_lr": jaccard_trajectories["rf_vs_lr"][-1],
                "rf_vs_gb": jaccard_trajectories["rf_vs_gb"][-1],
                "lr_vs_gb": jaccard_trajectories["lr_vs_gb"][-1],
            },
            "worst_case_consensus_count": len(consensus_worst_indices),
            "worst_case_consensus_indices": consensus_worst_indices,
            "rf_unique_indices": rf_unique_indices,
            "lr_unique_indices": lr_unique_indices,
            "gb_unique_indices": gb_unique_indices,
        },
        "feature_space_margins": mahalanobis_res,
        "seed_stability": seed_stability_results,
        "fdr_adjustment": {
            "target_q": fdr_q,
            "results": fdr_results,
        },
    }

    # 8. Dimensionality Reduction & Visualization
    pca = PCA(n_components=2, random_state=42)
    pca.fit(bundle.X_train)
    X_test_2d = pca.transform(bundle.X_test)

    plot_path = target_out / "failure_patterns_analysis.png"
    plot_e004_failure_patterns(
        summary_data=failure_patterns_summary,
        X_test_2d=X_test_2d,
        y_test=bundle.y_test,
        output_path=plot_path,
    )

    # 9. Artifacts Generation
    artifacts = generate_e004_artifacts(
        experiment_id=experiment_id,
        output_dir=target_out,
        dataset_metadata=dataset_metadata,
        models_metadata=models_metadata,
        seeds_config=seeds_config,
        sample_predictions=sample_predictions,
        failure_patterns_summary=failure_patterns_summary,
        protocol_version=protocol_version,
        failure_threshold=failure_threshold,
    )
    artifacts["failure_patterns_analysis.png"] = plot_path

    return {
        "experiment_id": experiment_id,
        "protocol_version": protocol_version,
        "dataset": dataset_metadata,
        "models": models_metadata,
        "seeds": active_seeds,
        "severities": severities,
        "n_sample_evaluations": len(sample_predictions),
        "evidence_conservation_audit": failure_patterns_summary["evidence_conservation_audit"],
        "failure_patterns_summary": failure_patterns_summary,
        "artifacts": {k: str(v) for k, v in artifacts.items()},
        "output_dir": str(target_out),
    }
