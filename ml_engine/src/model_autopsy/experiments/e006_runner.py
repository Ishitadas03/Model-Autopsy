"""Experiment E006 orchestrator: Systematic Distribution Shift (RQ6)."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.stats as stats
import yaml

from model_autopsy.analysis.distribution_shift import (
    calculate_audc,
    compute_directional_asymmetry_test,
    compute_dispersion_vs_translation_test,
    compute_friedman_test,
    compute_pairwise_model_tests,
    find_failure_boundary,
)
from model_autopsy.analysis.statistical import compute_sample_statistics
from model_autopsy.datasets.iris import load_and_validate_iris
from model_autopsy.metrics.evaluator import calculate_metrics
from model_autopsy.models.sklearn_gb import GradientBoostingAdapter, GradientBoostingConfig
from model_autopsy.models.sklearn_logistic import LogisticRegressionAdapter, LogisticRegressionConfig
from model_autopsy.models.sklearn_rf import RandomForestAdapter, RandomForestConfig
from model_autopsy.reporting.artifacts import generate_e006_artifacts
from model_autopsy.stress_tests.distribution_shift.covariate import (
    DIRECTION_VECTORS,
    TrainDistributionParameters,
    apply_directional_covariate_shift,
    apply_dispersion_covariate_shift,
    compute_selection_shift_weights,
)
from model_autopsy.stress_tests.noise.gaussian import apply_gaussian_noise
from model_autopsy.visualization.shift_plotter import plot_e006_distribution_shift


def run_e006_experiment(
    config_path: Optional[Path] = None,
    seeds: Optional[List[int]] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute the full preregistered Experiment E006 (RQ6).

    Protocol:
        1. Load dataset with frozen split_seed=42.
        2. Evaluate 3 architectures: Random Forest, Logistic Regression, Gradient Boosting.
        3. Sweep 5 independent research seeds: [42, 123, 456, 789, 1011].
        4. Apply 5 shift regimes across 7 severities: [0.00..0.30]:
           - directional_allometric
           - directional_petal_pos
           - directional_petal_neg
           - dispersion_dilation
           - selection_bias
        5. Guarantee strict baseline parity at s=0.00 (Delta_abs = 0.0000).
        6. Compute cell-level Macro-F1, Accuracy, Delta_abs, Delta_rel, and failure flags.
        7. Aggregate multi-seed statistics (Student's t 95% CIs with ddof=1, nu=4).
        8. Calculate AUDC, failure boundaries, Friedman omnibus tests, pairwise BH-FDR tests,
           directional asymmetry tests, and translation vs dispersion comparisons.
        9. Generate figures and canonical artifacts in artifacts/experiments/E006.

    Args:
        config_path: Path to YAML experiment configuration.
        seeds: List of research seeds (default: [42, 123, 456, 789, 1011]).
        output_dir: Destination directory for artifacts (default: artifacts/experiments/E006).

    Returns:
        Dictionary containing summary metrics and generated artifact paths.
    """
    # 1. Load config
    config: Dict[str, Any] = {}
    if config_path is not None and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

    exp_cfg = config.get("experiment", {})
    experiment_id = exp_cfg.get("id", "E006")
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
    q_threshold = float(eval_cfg.get("fdr_q_threshold", 0.05))

    if output_dir is not None:
        target_out = Path(output_dir)
    elif config.get("artifacts", {}).get("output_dir"):
        target_out = Path(config["artifacts"]["output_dir"])
    else:
        target_out = Path("artifacts/experiments/E006")

    target_out.mkdir(parents=True, exist_ok=True)

    # 2. Ingest Dataset
    bundle = load_and_validate_iris(split_seed=split_seed)
    X_train, y_train = bundle.X_train, bundle.y_train
    X_test, y_test = bundle.X_test, bundle.y_test

    # Strictly compute training distribution parameters
    train_params = TrainDistributionParameters.fit(X_train)
    train_mean = train_params.mean
    train_std = train_params.std
    train_pca = train_params.pca

    # Guarantee test immutability
    X_test.flags.writeable = False

    shift_regimes = [
        "directional_allometric",
        "directional_petal_pos",
        "directional_petal_neg",
        "dispersion_dilation",
        "selection_bias",
    ]

    model_configs = {
        "random_forest": {
            "name": "Random Forest",
            "constructor": lambda s: RandomForestAdapter(
                RandomForestConfig(
                    n_estimators=100,
                    criterion="gini",
                    max_depth=None,
                    bootstrap=True,
                    random_state=s,
                )
            ),
        },
        "logistic_regression": {
            "name": "Logistic Regression",
            "constructor": lambda s: LogisticRegressionAdapter(
                LogisticRegressionConfig(
                    C=1.0,
                    solver="lbfgs",
                    max_iter=1000,
                    random_state=s,
                )
            ),
        },
        "gradient_boosting": {
            "name": "Gradient Boosting",
            "constructor": lambda s: GradientBoostingAdapter(
                GradientBoostingConfig(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=3,
                    subsample=1.0,
                    random_state=s,
                )
            ),
        },
    }

    # 3. Execution grid: Models x Regimes x Severities x Seeds
    execution_records: List[Dict[str, Any]] = []
    # Structure for multi-seed aggregation: [model][regime][severity] -> list of metrics across seeds
    grid_store: Dict[str, Dict[str, Dict[float, List[Dict[str, Any]]]]] = {
        m: {r: {float(s): [] for s in severities} for r in shift_regimes}
        for m in model_configs
    }
    # Clean baseline tracker: [model] -> list of clean Macro-F1 across seeds
    clean_baselines: Dict[str, List[float]] = {m: [] for m in model_configs}
    # Matched benchmark noise tracker for H3: [model][severity] -> list of noise Macro-F1
    noise_benchmark: Dict[str, Dict[float, List[float]]] = {
        m: {float(s): [] for s in severities} for m in model_configs
    }

    print(f"Executing E006 across {len(model_configs)} models, {len(shift_regimes)} regimes, "
          f"{len(severities)} severities, {len(active_seeds)} seeds...")

    for seed in active_seeds:
        for model_id, m_spec in model_configs.items():
            model = m_spec["constructor"](seed)
            model.fit(X_train, y_train)

            # Evaluate clean baseline on frozen uncorrupted test set
            y_pred_clean = model.predict(X_test)
            clean_eval = calculate_metrics(y_test, y_pred_clean, failure_threshold=failure_threshold)
            clean_f1 = clean_eval.macro_f1
            clean_baselines[model_id].append(clean_f1)

            # Benchmark noise evaluations for H3
            for s in severities:
                s_flt = float(s)
                if s_flt == 0.0:
                    noise_benchmark[model_id][s_flt].append(clean_f1)
                else:
                    X_noise = apply_gaussian_noise(X_test, train_std, s_flt, seed=seed).X_corrupted
                    y_pred_noise = model.predict(X_noise)
                    noise_eval = calculate_metrics(y_test, y_pred_noise, baseline_macro_f1=clean_f1, failure_threshold=failure_threshold)
                    noise_benchmark[model_id][s_flt].append(noise_eval.macro_f1)

            # Evaluate each shift regime
            for regime in shift_regimes:
                for s in severities:
                    s_flt = float(s)
                    weights: Optional[np.ndarray] = None

                    if regime == "directional_allometric":
                        X_eval = apply_directional_covariate_shift(X_test, train_std, "allometric", s_flt)
                    elif regime == "directional_petal_pos":
                        X_eval = apply_directional_covariate_shift(X_test, train_std, "petal_pos", s_flt)
                    elif regime == "directional_petal_neg":
                        X_eval = apply_directional_covariate_shift(X_test, train_std, "petal_neg", s_flt)
                    elif regime == "dispersion_dilation":
                        X_eval = apply_dispersion_covariate_shift(X_test, train_mean, s_flt)
                    elif regime == "selection_bias":
                        # In selection shift, test points are not coordinate-displaced; instead, sample weights are used
                        X_eval = X_test
                        weights = compute_selection_shift_weights(X_test, train_pca, s_flt)
                    else:
                        raise ValueError(f"Unknown regime {regime}")

                    y_pred = model.predict(X_eval)
                    eval_res = calculate_metrics(
                        y_true=y_test,
                        y_pred=y_pred,
                        baseline_macro_f1=clean_f1,
                        failure_threshold=failure_threshold,
                        sample_weight=weights,
                    )

                    # Strict baseline parity check at s=0.00
                    if s_flt == 0.0:
                        if abs(eval_res.macro_f1 - clean_f1) > 1e-9:
                            raise AssertionError(
                                f"Baseline parity violated at s=0.00 for model {model_id}, regime {regime}, seed {seed}: "
                                f"{eval_res.macro_f1} vs {clean_f1}"
                            )

                    cell_rec = {
                        "model": model_id,
                        "shift_regime": regime,
                        "severity": s_flt,
                        "seed": seed,
                        "macro_f1": eval_res.macro_f1,
                        "accuracy": eval_res.accuracy,
                        "absolute_degradation_pp": eval_res.absolute_degradation_pp,
                        "relative_degradation_pct": eval_res.relative_degradation_pct,
                        "is_failed": eval_res.is_failed,
                    }
                    execution_records.append(cell_rec)
                    grid_store[model_id][regime][s_flt].append(cell_rec)

    total_cells = len(execution_records)
    print(f"Completed {total_cells} evaluation cells successfully.")

    # 4. Multi-seed Statistical Aggregation
    summary_models: Dict[str, Any] = {}
    audc_summary: Dict[str, Dict[str, float]] = {m: {} for m in model_configs}
    failure_boundaries: Dict[str, Dict[str, Optional[float]]] = {m: {} for m in model_configs}

    for model_id, m_spec in model_configs.items():
        clean_mean = float(np.mean(clean_baselines[model_id]))
        regimes_summary: Dict[str, Any] = {}

        for regime in shift_regimes:
            mean_macro_f1 = []
            ci_lower = []
            ci_upper = []
            mean_drops = []
            seed_terminal_drops = []
            seed_audcs = []

            for s in severities:
                s_flt = float(s)
                recs = grid_store[model_id][regime][s_flt]
                f1_vals = [r["macro_f1"] for r in recs]
                drop_vals = [r["absolute_degradation_pp"] for r in recs]

                stats_f1 = compute_sample_statistics(f1_vals)
                mean_macro_f1.append(stats_f1.mean)
                ci_lower.append(stats_f1.ci_lower)
                ci_upper.append(stats_f1.ci_upper)
                mean_drops.append(float(np.mean(drop_vals)))

                if s_flt == max(severities):
                    seed_terminal_drops = drop_vals

            # Compute AUDC per seed and overall mean AUDC
            for seed_idx in range(len(active_seeds)):
                seed_drops_curve = [
                    grid_store[model_id][regime][float(s)][seed_idx]["absolute_degradation_pp"]
                    for s in severities
                ]
                audc_val = calculate_audc(severities, seed_drops_curve)
                seed_audcs.append(audc_val)

            mean_audc = float(np.mean(seed_audcs))
            audc_summary[model_id][regime] = round(mean_audc, 4)

            # Failure boundary
            fb = find_failure_boundary(severities, mean_macro_f1, threshold=failure_threshold)
            failure_boundaries[model_id][regime] = fb

            terminal_drop_sem = float(np.std(seed_terminal_drops, ddof=1) / np.sqrt(len(active_seeds))) if len(active_seeds) > 1 else 0.0

            regimes_summary[regime] = {
                "mean_macro_f1": [round(v, 4) for v in mean_macro_f1],
                "ci_lower": [round(v, 4) for v in ci_lower],
                "ci_upper": [round(v, 4) for v in ci_upper],
                "mean_drops": [round(v, 4) for v in mean_drops],
                "terminal_macro_f1_mean": round(mean_macro_f1[-1], 4),
                "mean_terminal_drop": round(float(np.mean(seed_terminal_drops)), 4),
                "terminal_drop_sem": round(terminal_drop_sem, 4),
                "seed_terminal_drops": [round(v, 4) for v in seed_terminal_drops],
                "audc": round(mean_audc, 4),
                "seed_audcs": [round(v, 4) for v in seed_audcs],
                "failure_boundary": fb,
            }

        # Benchmark noise mean curve for Figure 3
        noise_mean_curve = [
            round(float(np.mean(noise_benchmark[model_id][float(s)])), 4)
            for s in severities
        ]

        summary_models[model_id] = {
            "name": m_spec["name"],
            "clean_macro_f1_mean": round(clean_mean, 4),
            "benchmark_noise_macro_f1": noise_mean_curve,
            "regimes": regimes_summary,
        }

    # 5. Hypothesis Testing
    # H1: Friedman omnibus test across models at terminal severity under directional shift (petal_pos)
    h1_model_terminal_drops = {
        m: summary_models[m]["regimes"]["directional_petal_pos"]["seed_terminal_drops"]
        for m in model_configs
    }
    h1_friedman = compute_friedman_test(h1_model_terminal_drops)
    h1_pairwise = compute_pairwise_model_tests(h1_model_terminal_drops, q_threshold=q_threshold)

    # H2: Directional asymmetry along petal axis (+petal vs -petal)
    # Pool across all models and seeds to evaluate general asymmetry
    all_pos_drops: List[float] = []
    all_neg_drops: List[float] = []
    for m in model_configs:
        all_pos_drops.extend(summary_models[m]["regimes"]["directional_petal_pos"]["seed_terminal_drops"])
        all_neg_drops.extend(summary_models[m]["regimes"]["directional_petal_neg"]["seed_terminal_drops"])
    h2_asymmetry = compute_directional_asymmetry_test(all_pos_drops, all_neg_drops)

    # H3: Shift vs Noise Comparison
    all_shift_audcs = []
    all_noise_audcs = []
    for m in model_configs:
        all_shift_audcs.extend(summary_models[m]["regimes"]["directional_petal_pos"]["seed_audcs"])
        # Compute seed AUDCs for noise
        for seed_idx in range(len(active_seeds)):
            seed_noise_drops = [
                (clean_baselines[m][seed_idx] - noise_benchmark[m][float(s)][seed_idx]) * 100.0
                for s in severities
            ]
            all_noise_audcs.append(calculate_audc(severities, seed_noise_drops))

    t_noise_res = stats.ttest_rel(all_shift_audcs, all_noise_audcs)
    h3_shift_vs_noise = {
        "test": "Paired Shift vs Noise AUDC Test (H3)",
        "mean_shift_audc": round(float(np.mean(all_shift_audcs)), 4),
        "mean_noise_audc": round(float(np.mean(all_noise_audcs)), 4),
        "mean_difference": round(float(np.mean(all_shift_audcs) - np.mean(all_noise_audcs)), 4),
        "t_statistic": round(float(t_noise_res.statistic), 4),
        "p_value": round(float(t_noise_res.pvalue), 6),
        "null_rejected": bool(t_noise_res.pvalue < 0.05),
    }

    # H4: Translation vs Dispersion AUDC
    all_trans_audcs = []
    all_disp_audcs = []
    for m in model_configs:
        all_trans_audcs.extend(summary_models[m]["regimes"]["directional_petal_pos"]["seed_audcs"])
        all_disp_audcs.extend(summary_models[m]["regimes"]["dispersion_dilation"]["seed_audcs"])
    h4_disp_vs_trans = compute_dispersion_vs_translation_test(all_trans_audcs, all_disp_audcs)

    hypothesis_tests = {
        "h1_friedman": h1_friedman,
        "h1_pairwise_comparisons": h1_pairwise,
        "h2_asymmetry": h2_asymmetry,
        "h3_shift_vs_noise": h3_shift_vs_noise,
        "h4_dispersion_vs_translation": h4_disp_vs_trans,
    }

    e006_summary = {
        "experiment_id": experiment_id,
        "protocol_version": protocol_version,
        "severities": severities,
        "shift_regimes": shift_regimes,
        "models": summary_models,
        "audc_summary": audc_summary,
        "failure_boundaries": failure_boundaries,
        "hypothesis_tests": hypothesis_tests,
    }

    # 6. Generate Figures
    figure_paths = plot_e006_distribution_shift(e006_summary, output_dir=target_out)

    # 7. Generate Artifacts
    artifact_paths = generate_e006_artifacts(
        experiment_id=experiment_id,
        output_dir=target_out,
        dataset_metadata={
            "name": dataset_cfg.get("name", "iris"),
            "n_instances": dataset_cfg.get("n_instances", 150),
            "n_features": dataset_cfg.get("n_features", 4),
            "n_classes": dataset_cfg.get("n_classes", 3),
            "split": dataset_cfg.get("split", {}),
        },
        models_metadata={m: config.get("models", {}).get(m, {}) for m in model_configs},
        seeds_config={"split_seed": split_seed, "research_seeds": active_seeds},
        stress_config=stress_cfg,
        e006_execution_records=execution_records,
        e006_summary=e006_summary,
        protocol_version=protocol_version,
        failure_threshold=failure_threshold,
    )

    all_artifacts = {**artifact_paths, **figure_paths}

    return {
        "status": "COMPLETED",
        "experiment_id": experiment_id,
        "protocol_version": protocol_version,
        "total_evaluation_cells": total_cells,
        "output_dir": str(target_out),
        "artifacts": {k: str(v) for k, v in all_artifacts.items()},
        "summary": e006_summary,
    }
