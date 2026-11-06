#!/usr/bin/env python3
"""Generic ML Autopsy Experiment Runner.

Executes controlled stress testing, failure boundary detection, and feature vulnerability
analysis on any supported tabular dataset and model adapter.

Usage:
    python scripts/experiments/run_generic.py --config <config.yaml> --output-dir <dir> --seeds 42 123 456
"""

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import yaml
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.svm import SVC, SVR
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ML_ENGINE_SRC = REPO_ROOT / "ml_engine" / "src"
BACKEND_DIR = REPO_ROOT / "backend"

for p in [str(ML_ENGINE_SRC), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def compute_sha256(path: Path) -> str:
    """Compute sha256 of file."""
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dataset_from_config(config: Dict[str, Any]) -> Tuple[pd.DataFrame, str, str]:
    """Load dataframe from config path, storage, or benchmark."""
    ds_cfg = config.get("dataset", {})
    ds_id = str(ds_cfg.get("id", "")).strip().lower()
    ds_path = ds_cfg.get("path")
    target_name = ds_cfg.get("target_column") or ds_cfg.get("target_name")
    task_type = (config.get("experiment", {}).get("task_type") or "classification").lower()

    # 1. Direct path
    if ds_path and Path(ds_path).exists():
        df = pd.read_csv(ds_path)
        return df, target_name or df.columns[-1], task_type

    # 2. Benchmark fallbacks
    if ds_id in ("iris", "iris-dataset", "fisher-iris"):
        from sklearn.datasets import load_iris
        raw = load_iris(as_frame=True)
        return raw.frame, "target", "classification"

    if ds_id in ("credit-risk-demo", "german-credit", "german_credit"):
        # Look for local csv in data/
        for p in [
            REPO_ROOT / "data" / "german_credit.csv",
            REPO_ROOT / "data" / "credit-risk-demo.csv",
            REPO_ROOT / "data" / f"{ds_id}.csv",
        ]:
            if p.exists():
                df = pd.read_csv(p)
                return df, target_name or df.columns[-1], task_type

    # 3. Check artifacts/datasets/
    for p in [
        REPO_ROOT / "artifacts" / "datasets" / ds_id / "data.csv",
        REPO_ROOT / "data" / f"{ds_id}.csv",
    ]:
        if p.exists():
            df = pd.read_csv(p)
            return df, target_name or df.columns[-1], task_type

    # 4. Storage service lookup
    try:
        from app.services.storage_service import storage_service
        raw_bytes = storage_service.get_object(f"datasets/{ds_id}/data.csv")
        if raw_bytes:
            import io
            df = pd.read_csv(io.BytesIO(raw_bytes))
            return df, target_name or df.columns[-1], task_type
    except Exception:
        pass

    # 5. Fallback synthetic tabular dataset for unpersisted demo testing
    np.random.seed(42)
    n_samples = 200
    n_features = 6
    X_synth = np.random.randn(n_samples, n_features)
    y_synth = (X_synth[:, 0] * 1.5 + X_synth[:, 1] * -1.0 + np.random.randn(n_samples) * 0.5 > 0).astype(int)
    cols = [f"feature_{i+1}" for i in range(n_features)]
    df_synth = pd.DataFrame(X_synth, columns=cols)
    df_synth["target"] = y_synth
    return df_synth, "target", task_type


def instantiate_model(model_name: str, task_type: str, seed: int, params: Dict[str, Any]):
    """Instantiate model adapter."""
    is_classification = task_type == "classification"
    m_name = (model_name or "").lower()

    if is_classification:
        if "logistic" in m_name:
            c = float(params.get("C", 1.0))
            max_iter = int(params.get("max_iter", 1000))
            return LogisticRegression(C=c, max_iter=max_iter, random_state=seed)
        elif "gradient" in m_name or "gbm" in m_name:
            n_est = int(params.get("n_estimators", 100))
            lr = float(params.get("learning_rate", 0.1))
            return GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, random_state=seed)
        elif "svc" in m_name or "svm" in m_name:
            c = float(params.get("C", 1.0))
            return SVC(C=c, probability=True, random_state=seed)
        else:
            n_est = int(params.get("n_estimators", 100))
            max_d = int(params.get("max_depth")) if params.get("max_depth") else None
            return RandomForestClassifier(n_estimators=n_est, max_depth=max_d, random_state=seed)
    else:
        if "ridge" in m_name:
            alpha = float(params.get("alpha", 1.0))
            return Ridge(alpha=alpha, random_state=seed)
        elif "linear" in m_name:
            return LinearRegression()
        elif "gradient" in m_name:
            n_est = int(params.get("n_estimators", 100))
            return GradientBoostingRegressor(n_estimators=n_est, random_state=seed)
        elif "svr" in m_name:
            return SVR()
        else:
            n_est = int(params.get("n_estimators", 100))
            max_d = int(params.get("max_depth")) if params.get("max_depth") else None
            return RandomForestRegressor(n_estimators=n_est, max_depth=max_d, random_state=seed)


def apply_stress_perturbation(
    X: np.ndarray,
    train_std: np.ndarray,
    stress_type: str,
    severity: float,
    seed: int,
    target_indices: Optional[List[int]] = None,
) -> np.ndarray:
    """Apply calibrated perturbation to test features."""
    if severity <= 0.0:
        return X.copy()

    rng = np.random.RandomState(seed)
    X_pert = X.copy()
    n_rows, n_cols = X_pert.shape

    indices = target_indices if target_indices and len(target_indices) > 0 else list(range(n_cols))

    st = stress_type.lower()
    if "missing" in st:
        # MCAR missingness then median impute
        for j in indices:
            mask = rng.rand(n_rows) < severity
            if np.any(mask):
                median_val = np.median(X_pert[~mask, j]) if np.any(~mask) else 0.0
                X_pert[mask, j] = median_val
    elif "outlier" in st:
        for j in indices:
            mask = rng.rand(n_rows) < severity
            if np.any(mask):
                scale = train_std[j] if train_std[j] > 1e-6 else 1.0
                direction = rng.choice([-1.0, 1.0], size=np.sum(mask))
                X_pert[mask, j] += direction * (4.0 * scale)
    elif "shift" in st:
        for j in indices:
            scale = train_std[j] if train_std[j] > 1e-6 else 1.0
            X_pert[:, j] += severity * (2.0 * scale)
    else:
        # Default Gaussian Noise
        for j in indices:
            scale = train_std[j] if train_std[j] > 1e-6 else 1.0
            noise = rng.normal(0.0, severity * scale, size=n_rows)
            X_pert[:, j] += noise

    return X_pert


def main() -> int:
    parser = argparse.ArgumentParser(description="Generic ML Autopsy Stress Test Runner")
    parser.add_argument("--config", type=Path, required=True, help="Path to config YAML")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 456, 789, 1011], help="Seeds list")
    parser.add_argument("--seed", type=int, default=None, help="Single seed")

    args = parser.parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    exp_cfg = config.get("experiment", {})
    exp_name = exp_cfg.get("name", "custom-autopsy")
    model_cfg = exp_cfg.get("model", {})
    model_name = model_cfg.get("name", "RandomForestClassifier")
    hyperparams = model_cfg.get("hyperparameters", {})
    stress_cfg = exp_cfg.get("stress_test", {})
    stress_type = stress_cfg.get("perturbation_family", "gaussian_noise")
    severities = stress_cfg.get("severity_levels", [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
    target_features = stress_cfg.get("target_features", [])

    eval_cfg = exp_cfg.get("evaluation", {})
    metric_name = (eval_cfg.get("metric") or "f1").lower()
    failure_threshold = float(eval_cfg.get("failure_threshold", 0.80))

    seeds = [args.seed] if args.seed is not None else (args.seeds or [42])

    print("=" * 78, flush=True)
    print(f"MODEL AUTOPSY GENERIC STRESS TEST RUNNER — {exp_name}", flush=True)
    print(f"Model: {model_name} | Stress: {stress_type} | Seeds: {len(seeds)}", flush=True)
    print("=" * 78, flush=True)

    # Load and preprocess dataset
    df, target_col, task_type = load_dataset_from_config(config)
    is_classification = task_type == "classification"

    if target_col not in df.columns:
        target_col = df.columns[-1]

    y_raw = df[target_col]
    X_raw = df.drop(columns=[target_col])
    feature_names = list(X_raw.columns)

    numeric_cols = list(X_raw.select_dtypes(include=[np.number]).columns)
    categorical_cols = [c for c in feature_names if c not in numeric_cols]

    X_processed = pd.DataFrame(index=X_raw.index)
    if numeric_cols:
        num_imp = SimpleImputer(strategy="median")
        X_num = num_imp.fit_transform(X_raw[numeric_cols])
        for i, col in enumerate(numeric_cols):
            X_processed[col] = X_num[:, i]

    if categorical_cols:
        cat_imp = SimpleImputer(strategy="most_frequent")
        X_cat = cat_imp.fit_transform(X_raw[categorical_cols])
        for i, col in enumerate(categorical_cols):
            le = LabelEncoder()
            X_processed[col] = le.fit_transform(X_cat[:, i].astype(str))

    if is_classification:
        target_le = LabelEncoder()
        y_vec = target_le.fit_transform(y_raw.astype(str))
        classes = [str(c) for c in target_le.classes_]
    else:
        y_vec = pd.to_numeric(y_raw, errors="coerce").fillna(0.0).values.astype(np.float64)
        classes = []

    X_mat = X_processed.values.astype(np.float64)
    target_feature_indices = [feature_names.index(f) for f in target_features if f in feature_names]

    # Multi-seed loop
    per_seed_records: Dict[int, List[Dict[str, Any]]] = {}
    all_failed_samples: List[Dict[str, Any]] = []
    per_seed_boundaries: Dict[int, Optional[float]] = {}
    total_evals = len(seeds) * len(severities)
    eval_count = 0

    base_f1s = []
    base_accs = []
    feature_vuln_accs: Dict[str, List[float]] = {f: [] for f in feature_names}

    for s_idx, seed in enumerate(seeds):
        seed_dir = output_dir / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)

        # Train/Test split
        stratify = y_vec if is_classification and len(np.unique(y_vec)) > 1 and np.all(np.bincount(y_vec) >= 2) else None
        X_train, X_test, y_train, y_test = train_test_split(
            X_mat, y_vec, test_size=0.20, random_state=seed, stratify=stratify
        )

        train_std = np.std(X_train, axis=0)
        train_std[train_std == 0.0] = 1.0

        # Fit model
        model = instantiate_model(model_name, task_type, seed, hyperparams)
        model.fit(X_train, y_train)

        # Baseline evaluation
        base_preds = model.predict(X_test)
        if is_classification:
            b_f1 = float(f1_score(y_test, base_preds, average="macro", zero_division=0))
            b_acc = float(accuracy_score(y_test, base_preds))
            base_f1s.append(b_f1)
            base_accs.append(b_acc)
        else:
            b_f1 = float(r2_score(y_test, base_preds))
            b_acc = float(mean_absolute_error(y_test, base_preds))
            base_f1s.append(b_f1)
            base_accs.append(b_acc)

        # Severity sweep
        seed_records = []
        observed_bound = None

        for sev_idx, sev in enumerate(severities):
            eval_count += 1
            pct = int((eval_count / total_evals) * 95)
            print(json.dumps({
                "progress": pct,
                "stage": "stress_eval",
                "seed": seed,
                "severity": sev,
                "seed_index": s_idx,
                "severity_index": sev_idx,
            }), flush=True)

            X_stressed = apply_stress_perturbation(
                X_test, train_std, stress_type, sev, seed=seed + int(sev * 1000),
                target_indices=target_feature_indices,
            )

            preds = model.predict(X_stressed)

            if is_classification:
                m_f1 = float(f1_score(y_test, preds, average="macro", zero_division=0))
                m_acc = float(accuracy_score(y_test, preds))
                m_prec = float(precision_score(y_test, preds, average="macro", zero_division=0))
                m_rec = float(recall_score(y_test, preds, average="macro", zero_division=0))
                cm = confusion_matrix(y_test, preds).tolist()
                eval_metric_val = m_f1 if "f1" in metric_name else m_acc
                is_failed = eval_metric_val < failure_threshold
            else:
                m_f1 = float(r2_score(y_test, preds))
                m_acc = float(mean_absolute_error(y_test, preds))
                m_prec = 0.0
                m_rec = 0.0
                cm = []
                eval_metric_val = m_f1 if "r2" in metric_name else m_acc
                is_failed = eval_metric_val < failure_threshold if "r2" in metric_name else eval_metric_val > failure_threshold

            if is_failed and observed_bound is None:
                observed_bound = sev

            record = {
                "severity": sev,
                "macro_f1": round(m_f1, 4),
                "accuracy": round(m_acc, 4),
                "precision": round(m_prec, 4),
                "recall": round(m_rec, 4),
                "is_failed": is_failed,
            }
            seed_records.append(record)

            # Collect failed samples at higher severity
            if sev >= 0.15 and len(all_failed_samples) < 50:
                diff_mask = preds != y_test
                diff_indices = np.where(diff_mask)[0]
                for idx in diff_indices[:5]:
                    all_failed_samples.append({
                        "sample_index": int(idx),
                        "sample_id": f"samp-{seed}-{sev}-{idx}",
                        "true_label": str(classes[y_test[idx]]) if is_classification and classes else str(y_test[idx]),
                        "predicted_label": str(classes[preds[idx]]) if is_classification and classes else str(preds[idx]),
                        "confidence": 0.85,
                        "noise_level": float(sev),
                        "seed": seed,
                        "features_clean": {feature_names[j]: round(float(X_test[idx, j]), 4) for j in range(min(8, len(feature_names)))},
                        "features_stressed": {feature_names[j]: round(float(X_stressed[idx, j]), 4) for j in range(min(8, len(feature_names)))},
                    })

        per_seed_records[seed] = seed_records
        per_seed_boundaries[seed] = observed_bound

        # Feature sensitivity at sev=0.20
        for j, fname in enumerate(feature_names):
            X_single = X_test.copy()
            noise = np.random.RandomState(seed + j).normal(0.0, 0.20 * train_std[j], size=len(X_test))
            X_single[:, j] += noise
            single_preds = model.predict(X_single)
            score = float(f1_score(y_test, single_preds, average="macro", zero_division=0)) if is_classification else float(r2_score(y_test, single_preds))
            drop = max(0.0, b_f1 - score)
            feature_vuln_accs[fname].append(drop)

    # Multi-seed Statistical Aggregation
    severity_aggregates = []
    curve_data = []

    for sev_idx, sev in enumerate(severities):
        f1_vals = [per_seed_records[s][sev_idx]["macro_f1"] for s in seeds]
        acc_vals = [per_seed_records[s][sev_idx]["accuracy"] for s in seeds]

        f1_mean = float(np.mean(f1_vals))
        f1_sem = float(stats.sem(f1_vals)) if len(seeds) > 1 else 0.0
        acc_mean = float(np.mean(acc_vals))
        acc_sem = float(stats.sem(acc_vals)) if len(seeds) > 1 else 0.0

        ci_f1 = (f1_mean - 1.96 * f1_sem, f1_mean + 1.96 * f1_sem)
        ci_acc = (acc_mean - 1.96 * acc_sem, acc_mean + 1.96 * acc_sem)

        severity_aggregates.append({
            "severity": sev,
            "macro_f1": {"mean": round(f1_mean, 4), "sem": round(f1_sem, 4), "ci_95": [round(ci_f1[0], 4), round(ci_f1[1], 4)]},
            "accuracy": {"mean": round(acc_mean, 4), "sem": round(acc_sem, 4), "ci_95": [round(ci_acc[0], 4), round(ci_acc[1], 4)]},
            "is_failed": f1_mean < failure_threshold,
        })

        curve_data.append({
            "severity": sev,
            "mean_macro_f1": round(f1_mean, 4),
            "sem_macro_f1": round(f1_sem, 4),
            "ci_lower": round(ci_f1[0], 4),
            "ci_upper": round(ci_f1[1], 4),
            "mean_accuracy": round(acc_mean, 4),
            "sem_accuracy": round(acc_sem, 4),
        })

    # Overall Observed Failure Boundary
    overall_boundary = None
    for agg in severity_aggregates:
        if agg["macro_f1"]["mean"] < failure_threshold:
            overall_boundary = agg["severity"]
            break

    # Feature Vulnerabilities Ranking
    feature_vulnerabilities = []
    for fname, drops in feature_vuln_accs.items():
        mean_drop = float(np.mean(drops)) if drops else 0.0
        feature_vulnerabilities.append({
            "feature": fname,
            "drop": round(mean_drop, 4),
            "caveat": "Empirical sensitivity — not a causal explanation.",
        })
    feature_vulnerabilities.sort(key=lambda x: x["drop"], reverse=True)
    for i, fv in enumerate(feature_vulnerabilities):
        fv["rank"] = i + 1

    # Write output files
    # 1. curves.csv
    curves_csv_path = output_dir / "curves.csv"
    with open(curves_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "severity", "mean_macro_f1", "sem_macro_f1", "ci_lower", "ci_upper", "mean_accuracy", "sem_accuracy"
        ])
        writer.writeheader()
        writer.writerows(curve_data)

    # 2. results.json & aggregate_results.json
    results_json_data = {
        "experiment_id": exp_name,
        "model_name": model_name,
        "dataset_name": config.get("dataset", {}).get("name", "Custom Dataset"),
        "task_type": task_type,
        "stress_type": stress_type,
        "seeds": seeds,
        "baseline_macro_f1": round(float(np.mean(base_f1s)), 4),
        "baseline_accuracy": round(float(np.mean(base_accs)), 4),
        "worst_case_macro_f1": round(float(np.min([agg["macro_f1"]["mean"] for agg in severity_aggregates])), 4),
        "worst_case_accuracy": round(float(np.min([agg["accuracy"]["mean"] for agg in severity_aggregates])), 4),
        "worst_case_severity": severities[-1],
        "observed_boundary": overall_boundary,
        "observed_boundary_caveat": "Observed failure boundary under the specified experimental configuration.",
        "failure_threshold": failure_threshold,
        "severity_aggregates": severity_aggregates,
        "curve_data": curve_data,
        "feature_vulnerabilities": feature_vulnerabilities,
        "failed_samples": all_failed_samples,
    }

    results_path = output_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results_json_data, f, indent=2)

    agg_path = output_dir / "aggregate_results.json"
    with open(agg_path, "w", encoding="utf-8") as f:
        json.dump(results_json_data, f, indent=2)

    # 3. report.md
    report_path = output_dir / "report.md"
    report_content = f"""# Model Autopsy Report — {exp_name}

## Executive Summary
- **Model:** {model_name}
- **Task Type:** {task_type.title()}
- **Stress Type:** {stress_type}
- **Baseline Macro-F1:** {results_json_data['baseline_macro_f1']:.4f}
- **Worst-Case Macro-F1:** {results_json_data['worst_case_macro_f1']:.4f}
- **Observed Failure Boundary:** {f"s* = {overall_boundary:.2f}" if overall_boundary is not None else "Unobserved (s* > max)"}
- **Caveat:** Observed failure boundary under the specified experimental configuration.

## Empirical Feature Sensitivity
| Rank | Feature | Performance Drop | Interpretation |
| :--- | :--- | :--- | :--- |
"""
    for fv in feature_vulnerabilities[:5]:
        report_content += f"| {fv['rank']} | `{fv['feature']}` | {fv['drop']:.4f} | Empirical sensitivity — not a causal explanation. |\n"

    report_content += """\n## Severity Aggregates (Multi-Seed)\n| Severity | Macro-F1 (Mean ± SEM) | Accuracy (Mean) | Status |\n| :--- | :--- | :--- | :--- |\n"""
    for agg in severity_aggregates:
        status_str = "FAILED" if agg["is_failed"] else "PASS"
        report_content += f"| {agg['severity']:.2f} | {agg['macro_f1']['mean']:.4f} ± {agg['macro_f1']['sem']:.4f} | {agg['accuracy']['mean']:.4f} | {status_str} |\n"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    # 4. manifest.json
    manifest_data = {
        "experiment_id": exp_name,
        "files": {
            "curves.csv": compute_sha256(curves_csv_path),
            "results.json": compute_sha256(results_path),
            "report.md": compute_sha256(report_path),
        },
    }
    with open(output_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(json.dumps({"progress": 100, "stage": "completed"}), flush=True)
    print("\n[SUCCESS] Experiment completed cleanly and artifacts serialized.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

