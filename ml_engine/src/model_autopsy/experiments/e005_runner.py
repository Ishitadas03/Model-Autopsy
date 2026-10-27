"""Experiment E005 orchestrator: Feature Vulnerability Analysis (RQ3)."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.stats as stats
import yaml

from model_autopsy.analysis.feature_vulnerability import (
    calculate_audc,
    compute_clean_importance_correlation,
    compute_feature_rankings,
    compute_friedman_test,
    compute_pairwise_feature_tests,
    compute_rank_concordance,
)
from model_autopsy.analysis.statistical import compute_sample_statistics
from model_autopsy.datasets.iris import load_and_validate_iris
from model_autopsy.metrics.evaluator import calculate_metrics
from model_autopsy.models.sklearn_gb import GradientBoostingAdapter, GradientBoostingConfig
from model_autopsy.models.sklearn_logistic import LogisticRegressionAdapter, LogisticRegressionConfig
from model_autopsy.models.sklearn_rf import RandomForestAdapter, RandomForestConfig
from model_autopsy.reporting.artifacts import generate_e005_artifacts
from model_autopsy.stress_tests.feature_corruption.single_feature import (
    apply_single_feature_gaussian_noise,
    apply_single_feature_missingness,
    apply_single_feature_outliers,
)
from model_autopsy.visualization.feature_plotter import plot_e005_feature_vulnerability


def run_e005_experiment(
    config_path: Optional[Path] = None,
    seeds: Optional[List[int]] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute the full preregistered Experiment E005 (RQ3).

    Protocol:
        1. Load dataset with frozen split_seed=42.
        2. Evaluate 3 architectures: Random Forest, Logistic Regression, Gradient Boosting.
        3. Sweep 5 independent research seeds: [42, 123, 456, 789, 1011].
        4. Apply 3 coordinate-isolated perturbation operators:
           - single_feature_gaussian_noise
           - single_feature_missingness
           - single_feature_outliers
        5. For each operator, perturb each of the 4 features across 7 severities: [0.00..0.30].
        6. Compute cell-level Macro-F1, Accuracy, Delta_abs, Delta_rel, and failure flags.
        7. Aggregate multi-seed statistics (Student's t 95% CIs with ddof=1, nu=4).
        8. Calculate AUDC, terminal rankings, Friedman omnibus tests, pairwise BH-FDR comparisons,
           and rank concordances.
        9. Generate figures and canonical artifacts in artifacts/experiments/E005.

    Args:
        config_path: Path to YAML experiment configuration.
        seeds: List of research seeds (default: [42, 123, 456, 789, 1011]).
        output_dir: Destination directory for artifacts (default: artifacts/experiments/E005).

    Returns:
        Dictionary containing summary metrics and generated artifact paths.
    """
    # 1. Load config
    config: Dict[str, Any] = {}
    if config_path is not None and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    exp_cfg = config.get("experiment", {})
    experiment_id = exp_cfg.get("id", "E005")
    protocol_version = exp_cfg.get("protocol_version", "1.0.0")

    dataset_cfg = config.get("dataset", {})
    split_seed = dataset_cfg.get("split", {}).get("split_seed", 42)

    seeds_cfg = config.get("seeds", {})
    configured_seeds = seeds_cfg.get("research_seeds", [42, 123, 456, 789, 1011])
    active_seeds = seeds if seeds is not None else configured_seeds

    stress_cfg = config.get("stress_tests", {})
    severities = stress_cfg.get("severities", [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
    primary_operator = stress_cfg.get("primary_operator", "single_feature_gaussian_noise")

    eval_cfg = config.get("evaluation", {})
    failure_threshold = float(eval_cfg.get("failure_threshold", 0.80))

    if output_dir is not None:
        target_out = Path(output_dir)
    elif config.get("artifacts", {}).get("output_dir"):
        target_out = Path(config["artifacts"]["output_dir"])
    else:
        target_out = Path("artifacts/experiments/E005")

    target_out.mkdir(parents=True, exist_ok=True)

    # 2. Ingest Dataset
    bundle = load_and_validate_iris(split_seed=split_seed)
    X_train, y_train = bundle.X_train, bundle.y_train
    X_test, y_test = bundle.X_test, bundle.y_test
    train_std = bundle.train_std
    train_mean = bundle.train_mean
    feature_names = bundle.feature_names
    target_names = bundle.target_names
    n_features = len(feature_names)

    # Operator mapping
    operators = {
        "single_feature_gaussian_noise": lambda X, j, s, seed: apply_single_feature_gaussian_noise(
            X, train_std=train_std, feature_index=j, severity=s, seed=seed
        ),
        "single_feature_missingness": lambda X, j, s, seed: apply_single_feature_missingness(
            X, train_mean=train_mean, feature_index=j, severity=s, seed=seed
        ),
        "single_feature_outliers": lambda X, j, s, seed: apply_single_feature_outliers(
            X, train_mean=train_mean, train_std=train_std, feature_index=j, severity=s, displacement_factor=5.0, seed=seed
        ),
    }

    # Model adapters factory
    def create_model(model_key: str, seed: int):
        if model_key == "random_forest":
            return RandomForestAdapter(config=RandomForestConfig(), seed=seed)
        elif model_key == "logistic_regression":
            return LogisticRegressionAdapter(config=LogisticRegressionConfig(), seed=seed)
        elif model_key == "gradient_boosting":
            return GradientBoostingAdapter(config=GradientBoostingConfig(), seed=seed)
        else:
            raise ValueError(f"Unknown model_key: {model_key}")

    model_keys = ["random_forest", "logistic_regression", "gradient_boosting"]

    # Data structures for collecting evaluation results
    # results[model][operator][feature_idx][severity] -> list of seed metrics
    raw_results: Dict[str, Dict[str, Dict[int, Dict[float, List[Dict[str, Any]]]]]] = {
        m: {op: {j: {s: [] for s in severities} for j in range(n_features)} for op in operators}
        for m in model_keys
    }

    # Track clean baselines per (model, seed)
    clean_baselines: Dict[str, Dict[int, float]] = {m: {} for m in model_keys}
    # Track clean feature importances per (model, seed)
    clean_importances_per_seed: Dict[str, Dict[int, np.ndarray]] = {m: {} for m in model_keys}

    # Track AUDC per (model, operator, feature_idx, seed)
    audc_per_seed: Dict[str, Dict[str, Dict[int, Dict[int, float]]]] = {
        m: {op: {j: {} for j in range(n_features)} for op in operators}
        for m in model_keys
    }

    total_cells = 0

    # 3. Main Evaluation Loop
    for m_id in model_keys:
        for seed in active_seeds:
            # Fit model on training data
            model = create_model(m_id, seed=seed)
            model.fit(X_train, y_train)

            # Evaluate clean baseline on pristine X_test
            clean_preds = model.predict(X_test)
            clean_metrics = calculate_metrics(y_test, clean_preds, baseline_macro_f1=1.0)
            baseline_f1 = clean_metrics.macro_f1
            clean_baselines[m_id][seed] = baseline_f1

            # Extract clean feature importance
            if m_id == "random_forest":
                raw_imp = model._model.feature_importances_
            elif m_id == "gradient_boosting":
                raw_imp = model._model.feature_importances_
            elif m_id == "logistic_regression":
                # Average absolute coefficient across classes
                coefs = np.abs(model._classifier.coef_)  # shape (n_classes, n_features)
                raw_imp = np.mean(coefs, axis=0)
                norm_sum = np.sum(raw_imp)
                if norm_sum > 0:
                    raw_imp = raw_imp / norm_sum
            clean_importances_per_seed[m_id][seed] = raw_imp

            # Sweep operators, features, severities
            for op_id, op_func in operators.items():
                for j in range(n_features):
                    degs_for_audc = []

                    for s in severities:
                        total_cells += 1
                        # Apply coordinate-isolated perturbation
                        pert_res = op_func(X_test, j, s, seed)
                        corrupted_X = pert_res.X_corrupted

                        # Invariant check: non-target features must be bitwise identical
                        non_target_mask = np.ones(n_features, dtype=bool)
                        non_target_mask[j] = False
                        if not np.array_equal(corrupted_X[:, non_target_mask], X_test[:, non_target_mask]):
                            raise RuntimeError(
                                f"Feature isolation violation: operator {op_id} altered non-target columns!"
                            )

                        # Predict and evaluate
                        preds = model.predict(corrupted_X)
                        cell_metrics = calculate_metrics(
                            y_test, preds, baseline_macro_f1=baseline_f1
                        )

                        delta_abs = max(0.0, baseline_f1 - cell_metrics.macro_f1)
                        delta_rel = (
                            (delta_abs / baseline_f1 * 100.0) if baseline_f1 > 0 else 0.0
                        )
                        is_failed = bool(cell_metrics.macro_f1 < failure_threshold)

                        degs_for_audc.append(delta_abs)

                        raw_results[m_id][op_id][j][s].append({
                            "seed": seed,
                            "macro_f1": cell_metrics.macro_f1,
                            "accuracy": cell_metrics.accuracy,
                            "delta_abs": delta_abs,
                            "delta_rel": delta_rel,
                            "is_failed": is_failed,
                        })

                    # Compute AUDC for this (model, op, feature, seed)
                    audc_val = calculate_audc(severities, degs_for_audc)
                    audc_per_seed[m_id][op_id][j][seed] = audc_val

    # 4. Statistical Aggregation
    summary_models: Dict[str, Any] = {}

    for m_id in model_keys:
        clean_scores = list(clean_baselines[m_id].values())
        clean_stat = compute_sample_statistics(clean_scores)

        # Average clean feature importance across seeds
        avg_clean_imp = np.mean(
            [clean_importances_per_seed[m_id][sd] for sd in active_seeds], axis=0
        )
        clean_imp_dict = {
            feature_names[j]: round(float(avg_clean_imp[j]), 4) for j in range(n_features)
        }

        m_summary = {
            "clean_macro_f1_mean": clean_stat.mean,
            "clean_macro_f1_std": clean_stat.sample_std,
            "clean_macro_f1_sem": clean_stat.sem,
            "clean_feature_importance": clean_imp_dict,
            "operators": {},
        }

        for op_id in operators:
            features_summary: Dict[str, Any] = {}
            # Matrix of terminal drops at s=0.30: shape (n_seeds, n_features)
            terminal_matrix = np.zeros((len(active_seeds), n_features), dtype=np.float64)
            # Matrix of AUDC: shape (n_seeds, n_features)
            audc_matrix = np.zeros((len(active_seeds), n_features), dtype=np.float64)

            feature_ranking_candidates = []
            audc_ranking_candidates = []

            for j, f_name in enumerate(feature_names):
                severity_aggregates = []

                for s_idx, s in enumerate(severities):
                    seed_runs = raw_results[m_id][op_id][j][s]
                    f1_vals = [r["macro_f1"] for r in seed_runs]
                    acc_vals = [r["accuracy"] for r in seed_runs]
                    d_abs_vals = [r["delta_abs"] for r in seed_runs]
                    d_rel_vals = [r["delta_rel"] for r in seed_runs]
                    fail_flags = [r["is_failed"] for r in seed_runs]

                    f1_stat = compute_sample_statistics(f1_vals)
                    acc_stat = compute_sample_statistics(acc_vals)
                    d_abs_stat = compute_sample_statistics(d_abs_vals)
                    d_rel_stat = compute_sample_statistics(d_rel_vals)

                    severity_aggregates.append({
                        "severity": s,
                        "macro_f1_mean": f1_stat.mean,
                        "macro_f1_std": f1_stat.sample_std,
                        "macro_f1_sem": f1_stat.sem,
                        "macro_f1_ci95_low": f1_stat.ci_lower,
                        "macro_f1_ci95_high": f1_stat.ci_upper,
                        "accuracy_mean": acc_stat.mean,
                        "delta_abs_mean": d_abs_stat.mean,
                        "delta_abs_std": d_abs_stat.sample_std,
                        "delta_abs_sem": d_abs_stat.sem,
                        "delta_abs_ci95_low": d_abs_stat.ci_lower,
                        "delta_abs_ci95_high": d_abs_stat.ci_upper,
                        "delta_rel_mean": d_rel_stat.mean,
                        "failure_count": sum(fail_flags),
                        "is_failed": bool(f1_stat.mean < failure_threshold),
                    })

                # Terminal severity stats (s = 0.30)
                term_agg = severity_aggregates[-1]
                for seed_idx, seed in enumerate(active_seeds):
                    terminal_matrix[seed_idx, j] = raw_results[m_id][op_id][j][severities[-1]][seed_idx]["delta_abs"]
                    audc_matrix[seed_idx, j] = audc_per_seed[m_id][op_id][j][seed]

                audc_vals_j = list(audc_per_seed[m_id][op_id][j].values())
                audc_stat = compute_sample_statistics(audc_vals_j)

                features_summary[f_name] = {
                    "feature_index": j,
                    "feature_name": f_name,
                    "audc_mean": audc_stat.mean,
                    "audc_std": audc_stat.sample_std,
                    "audc_sem": audc_stat.sem,
                    "audc_ci95_low": audc_stat.ci_lower,
                    "audc_ci95_high": audc_stat.ci_upper,
                    "terminal_delta_abs_mean": term_agg["delta_abs_mean"],
                    "terminal_delta_abs_sem": term_agg["delta_abs_sem"],
                    "severity_aggregates": severity_aggregates,
                }

                feature_ranking_candidates.append({
                    "feature_name": f_name,
                    "feature_index": j,
                    "delta_abs_mean": term_agg["delta_abs_mean"],
                    "sem": term_agg["delta_abs_sem"],
                    "ci95_low": term_agg["delta_abs_ci95_low"],
                    "ci95_high": term_agg["delta_abs_ci95_high"],
                    "audc": audc_stat.mean,
                })

                audc_ranking_candidates.append({
                    "feature_name": f_name,
                    "feature_index": j,
                    "audc_mean": audc_stat.mean,
                    "sem": audc_stat.sem,
                    "terminal_delta": term_agg["delta_abs_mean"],
                })

            # Formal Rankings
            terminal_rankings = compute_feature_rankings(feature_ranking_candidates, sort_by="delta_abs_mean")
            audc_rankings = compute_feature_rankings(audc_ranking_candidates, sort_by="audc_mean")

            # Friedman Test across features at s=0.30
            friedman_res = compute_friedman_test(terminal_matrix)

            # Pairwise comparisons with BH-FDR
            pairwise_res = compute_pairwise_feature_tests(
                terminal_matrix, feature_names=feature_names, alpha=0.05
            )

            # Clean importance vs stress vulnerability correlation (H3)
            clean_imp_vec = [clean_imp_dict[f_name] for f_name in feature_names]
            term_drop_vec = [features_summary[f_name]["terminal_delta_abs_mean"] for f_name in feature_names]
            clean_corr = compute_clean_importance_correlation(clean_imp_vec, term_drop_vec)

            m_summary["operators"][op_id] = {
                "features": features_summary,
                "terminal_rankings": terminal_rankings,
                "audc_rankings": audc_rankings,
                "friedman_test": friedman_res,
                "pairwise_comparisons": pairwise_res,
                "clean_importance_correlation": clean_corr,
            }

        summary_models[m_id] = m_summary

    # 5. Inter-Model Concordance (H2) under primary operator
    inter_model_concordance: Dict[str, Any] = {}
    for i in range(len(model_keys)):
        for k in range(i + 1, len(model_keys)):
            m_a = model_keys[i]
            m_b = model_keys[k]
            ranks_a = [
                r["rank"]
                for r in summary_models[m_a]["operators"][primary_operator]["terminal_rankings"]
            ]
            ranks_b = [
                r["rank"]
                for r in summary_models[m_b]["operators"][primary_operator]["terminal_rankings"]
            ]
            conc = compute_rank_concordance(ranks_a, ranks_b)
            inter_model_concordance[f"{m_a}_vs_{m_b}"] = conc

    # 6. Modality Concordance (H4) within each model
    modality_concordance: Dict[str, Any] = {}
    for m_id in model_keys:
        m_ops = summary_models[m_id]["operators"]
        ranks_noise = [r["rank"] for r in m_ops["single_feature_gaussian_noise"]["terminal_rankings"]]
        ranks_missing = [r["rank"] for r in m_ops["single_feature_missingness"]["terminal_rankings"]]
        ranks_outliers = [r["rank"] for r in m_ops["single_feature_outliers"]["terminal_rankings"]]

        modality_concordance[m_id] = {
            "noise_vs_missingness": compute_rank_concordance(ranks_noise, ranks_missing),
            "noise_vs_outliers": compute_rank_concordance(ranks_noise, ranks_outliers),
            "missingness_vs_outliers": compute_rank_concordance(ranks_missing, ranks_outliers),
        }

    # Complete execution summary dictionary
    e005_summary: Dict[str, Any] = {
        "experiment_id": experiment_id,
        "protocol_version": protocol_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_evaluation_cells": total_cells,
        "n_seeds": len(active_seeds),
        "seeds": active_seeds,
        "feature_names": feature_names,
        "target_names": target_names,
        "severities": severities,
        "primary_operator": primary_operator,
        "failure_threshold": failure_threshold,
        "models": summary_models,
        "inter_model_concordance": inter_model_concordance,
        "modality_concordance": modality_concordance,
    }

    # 7. Generate Figures
    figure_paths = plot_e005_feature_vulnerability(e005_summary, target_out)

    # 8. Generate Artifacts
    dataset_metadata = {
        "dataset_name": "iris",
        "n_instances": len(X_train) + len(X_test),
        "n_features": n_features,
        "n_classes": len(target_names),
        "feature_names": feature_names,
        "target_names": target_names,
        "test_indices": bundle.test_indices.tolist(),
        "dataset_hash": bundle.dataset_hash,
    }
    models_metadata = {
        "random_forest": {"adapter": "sklearn_rf", "n_estimators": 100},
        "logistic_regression": {"adapter": "sklearn_logistic", "preprocessing": "StandardScaler"},
        "gradient_boosting": {"adapter": "sklearn_gb", "n_estimators": 100},
    }
    seeds_config = {
        "split_seed": split_seed,
        "research_seeds": active_seeds,
    }

    artifact_paths = generate_e005_artifacts(
        experiment_id=experiment_id,
        output_dir=target_out,
        dataset_metadata=dataset_metadata,
        models_metadata=models_metadata,
        seeds_config=seeds_config,
        e005_summary=e005_summary,
        protocol_version=protocol_version,
        failure_threshold=failure_threshold,
    )

    artifact_paths.update(figure_paths)

    return {
        "experiment_id": experiment_id,
        "status": "completed",
        "output_dir": str(target_out),
        "total_evaluation_cells": total_cells,
        "n_models": len(model_keys),
        "n_operators": len(operators),
        "n_features": n_features,
        "n_severities": len(severities),
        "n_seeds": len(active_seeds),
        "artifacts": {k: str(v) for k, v in artifact_paths.items()},
        "e005_summary": e005_summary,
    }
