"""Artifact generation and reproducibility manifest serialization for Model Autopsy."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Dict, List, Optional
import numpy as np


def get_git_commit_hash() -> str:
    """Retrieve current Git commit SHA without altering repository state."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return "uncommitted"


def get_environment_metadata() -> Dict[str, Any]:
    """Capture runtime environment details and library versions without leaking secrets."""
    packages = {}
    for pkg in ["numpy", "scipy", "scikit-learn", "pandas", "matplotlib", "pydantic", "yaml"]:
        try:
            if pkg == "scikit-learn":
                import sklearn
                packages["scikit-learn"] = getattr(sklearn, "__version__", "unknown")
            elif pkg == "yaml":
                import yaml
                packages["pyyaml"] = getattr(yaml, "__version__", "unknown")
            else:
                mod = __import__(pkg)
                packages[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            packages[pkg] = "not_installed"

    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "os_system": platform.system(),
        "architecture": platform.machine(),
        "package_versions": packages,
    }


def generate_artifacts(
    experiment_id: str,
    output_dir: Path,
    dataset_metadata: Dict[str, Any],
    model_metadata: Dict[str, Any],
    seeds_config: Dict[str, Any],
    severity_records: List[Dict[str, Any]],
    failure_boundary_result: Dict[str, Any],
    feature_vulnerabilities: List[Dict[str, Any]],
    baseline_metrics: Dict[str, Any],
    protocol_version: str = "1.0.0",
    failure_threshold: float = 0.80,
) -> Dict[str, Path]:
    """Synthesize and serialize all machine-readable artifacts and research reports.

    Generates:
        - results.csv (and severity_metrics.csv)
        - results.json
        - manifest.json
        - baseline_metrics.json
        - robustness_curve.json
        - confusion_matrices/cm_s*.json
        - failure_analysis.json
        - report.md

    Args:
        experiment_id: Unique experiment identifier (e.g. 'E001').
        output_dir: Root directory for artifact emission.
        dataset_metadata: Dataset names, shapes, checksums, and dispersion vectors.
        model_metadata: Model architecture, hyperparameters, and adapter details.
        seeds_config: Split seed, model seed, noise seed, and planned research seeds.
        severity_records: Complete per-severity evaluation results.
        failure_boundary_result: Failure boundary findings and messages.
        feature_vulnerabilities: Ranked empirical feature vulnerability analysis.
        baseline_metrics: Baseline metrics achieved at s=0.00.
        protocol_version: Scientific protocol version string.
        failure_threshold: Strict reliability cutoff (default 0.80).

    Returns:
        Dictionary mapping artifact keys to their absolute Path objects.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cm_dir = output_dir / "confusion_matrices"
    cm_dir.mkdir(parents=True, exist_ok=True)

    artifacts: Dict[str, Path] = {}

    # 1. results.csv & severity_metrics.csv
    csv_headers = [
        "severity",
        "macro_f1",
        "accuracy",
        "absolute_degradation_pp",
        "relative_degradation_pct",
        "is_failed",
        "rel_drop_exceeds_15_pct",
    ]

    for fname in ["results.csv", "severity_metrics.csv"]:
        csv_path = output_dir / fname
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_headers, extrasaction="ignore")
            writer.writeheader()
            for record in severity_records:
                writer.writerow(record)
        artifacts[fname] = csv_path

    # 2. baseline_metrics.json
    baseline_path = output_dir / "baseline_metrics.json"
    with open(baseline_path, "w", encoding="utf-8") as f:
        json.dump(baseline_metrics, f, indent=2)
    artifacts["baseline_metrics.json"] = baseline_path

    # 3. robustness_curve.json
    curve_coords = [
        {
            "severity": float(r["severity"]),
            "macro_f1": float(r["macro_f1"]),
            "accuracy": float(r["accuracy"]),
            "absolute_degradation_pp": float(r["absolute_degradation_pp"]),
            "relative_degradation_pct": float(r["relative_degradation_pct"]),
        }
        for r in severity_records
    ]
    curve_json_path = output_dir / "robustness_curve.json"
    with open(curve_json_path, "w", encoding="utf-8") as f:
        json.dump({"curve_data": curve_coords, "threshold": failure_threshold}, f, indent=2)
    artifacts["robustness_curve.json"] = curve_json_path

    # 4. confusion_matrices/cm_s*.json
    for r in severity_records:
        sev = float(r["severity"])
        sev_tag = f"s{int(round(sev * 100)):02d}"
        cm_file = cm_dir / f"cm_{sev_tag}.json"
        with open(cm_file, "w", encoding="utf-8") as f:
            json.dump({
                "severity": sev,
                "confusion_matrix": r.get("confusion_matrix", []),
                "class_names": dataset_metadata.get("target_names", []),
            }, f, indent=2)

    # 5. failure_analysis.json
    failure_analysis_data = {
        "experiment_id": experiment_id,
        "failure_boundary": failure_boundary_result,
        "feature_vulnerabilities": feature_vulnerabilities,
        "scientific_captions": {
            "boundary_caption": "Observed failure boundary under the specified experimental configuration.",
            "sensitivity_caveat": "Empirical sensitivity — not a causal explanation.",
        },
    }
    failure_analysis_path = output_dir / "failure_analysis.json"
    with open(failure_analysis_path, "w", encoding="utf-8") as f:
        json.dump(failure_analysis_data, f, indent=2)
    artifacts["failure_analysis.json"] = failure_analysis_path

    # 6. results.json
    results_json_data = {
        "experiment_id": experiment_id,
        "protocol_version": protocol_version,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset_metadata.get("name", "iris"),
        "model": model_metadata.get("class_name", "RandomForestClassifier"),
        "failure_threshold": failure_threshold,
        "baseline_macro_f1": baseline_metrics.get("macro_f1"),
        "baseline_accuracy": baseline_metrics.get("accuracy"),
        "observed_failure_boundary": failure_boundary_result.get("observed_boundary"),
        "is_boundary_observed": failure_boundary_result.get("is_boundary_observed"),
        "severities_evaluated": [r["severity"] for r in severity_records],
        "severity_results": severity_records,
        "feature_vulnerabilities": feature_vulnerabilities,
        "boundary_caption": "Observed failure boundary under the specified experimental configuration.",
    }
    results_json_path = output_dir / "results.json"
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results_json_data, f, indent=2)
    artifacts["results.json"] = results_json_path

    # 7. manifest.json
    manifest_data = {
        "experiment_id": experiment_id,
        "experiment_name": "Gaussian Noise Robustness Evaluation of Random Forest on Iris",
        "protocol_version": protocol_version,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit_hash": get_git_commit_hash(),
        "environment": get_environment_metadata(),
        "dataset": dataset_metadata,
        "model": model_metadata,
        "noise_definition": {
            "family": "additive_gaussian_noise",
            "mathematical_formula": "epsilon_ij ~ Normal(0, (severity * train_std[j])^2)",
            "dispersion_source": "train_partition_strictly",
            "dispersion_degrees_of_freedom": "ddof=1",
            "evaluated_severities": [r["severity"] for r in severity_records],
        },
        "seeds": seeds_config,
        "evaluation_criteria": {
            "primary_metric": "macro_f1",
            "secondary_metrics": ["accuracy", "confusion_matrix"],
            "failure_threshold": failure_threshold,
            "failure_rule": "macro_f1 < failure_threshold (strict less-than)",
            "relative_drop_diagnostic_threshold_pct": 15.0,
        },
        "observed_failure_boundary": failure_boundary_result.get("observed_boundary"),
        "boundary_caption": "Observed failure boundary under the specified experimental configuration.",
        "artifacts_generated": {k: str(v.name) for k, v in artifacts.items()},
        "scientific_limitations": [
            "Benchmark scale: Iris is a 4-feature, 150-instance benchmark; findings do not generalize across high-dimensional non-tabular domains.",
            "Evaluation discretization: With N_test=30 (10/class), each misclassification changes metric by 3.33 percentage points.",
            "Noise specificity: Additive isotropic Gaussian noise is a synthetic model and does not reflect structured or adversarial shifts.",
            "Observational nature: Feature sensitivities reflect empirical variance and must not be interpreted causally.",
        ],
    }
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    artifacts["manifest.json"] = manifest_path

    # 8. report.md
    report_path = output_dir / "report.md"
    report_content = generate_markdown_report(
        experiment_id=experiment_id,
        protocol_version=protocol_version,
        dataset_metadata=dataset_metadata,
        model_metadata=model_metadata,
        seeds_config=seeds_config,
        severity_records=severity_records,
        failure_boundary_result=failure_boundary_result,
        feature_vulnerabilities=feature_vulnerabilities,
        baseline_metrics=baseline_metrics,
        failure_threshold=failure_threshold,
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    artifacts["report.md"] = report_path

    return artifacts


def generate_markdown_report(
    experiment_id: str,
    protocol_version: str,
    dataset_metadata: Dict[str, Any],
    model_metadata: Dict[str, Any],
    seeds_config: Dict[str, Any],
    severity_records: List[Dict[str, Any]],
    failure_boundary_result: Dict[str, Any],
    feature_vulnerabilities: List[Dict[str, Any]],
    baseline_metrics: Dict[str, Any],
    failure_threshold: float,
) -> str:
    """Construct rigorous scientific markdown report from verified evaluation runs."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    b_f1 = baseline_metrics.get("macro_f1", 0.0)
    b_acc = baseline_metrics.get("accuracy", 0.0)
    worst_record = min(severity_records, key=lambda r: float(r["macro_f1"]))
    worst_f1 = worst_record["macro_f1"]
    worst_sev = worst_record["severity"]

    # Table rows
    table_rows = []
    for r in severity_records:
        sev = r["severity"]
        f1 = r["macro_f1"]
        acc = r["accuracy"]
        d_abs = r["absolute_degradation_pp"]
        d_rel = r["relative_degradation_pct"]
        status = "**FAIL**" if r["is_failed"] else "PASS"
        rel_flag = "⚠️ Yes (>15%)" if r["rel_drop_exceeds_15_pct"] else "No"
        table_rows.append(
            f"| `{sev:.2f}` | `{f1:.4f}` | `{acc:.4f}` | `{d_abs:+.2f} pp` | `{d_rel:+.2f}%` | {status} | {rel_flag} |"
        )
    table_block = "\n".join(table_rows)

    # Feature rows
    feature_rows = []
    for v in feature_vulnerabilities:
        feature_rows.append(
            f"| {v.get('rank', '-')} | `{v['feature']}` | `{(v['drop'] * 100):.2f} pp` | `{v['macro_f1_isolated']:.4f}` |"
        )
    feature_table_block = "\n".join(feature_rows)

    obs_b = failure_boundary_result.get("observed_boundary")
    if obs_b is not None:
        boundary_text = f"**`s* = {obs_b:.2f}`**"
    else:
        boundary_text = f"**Not observed within tested severity range (`s* > {max(r['severity'] for r in severity_records):.2f}`)**"

    return rf"""# Empirical Research Report: {experiment_id}
> **Title:** Empirical Characterization of Random Forest Classifier Robustness Under Additive Gaussian Feature Noise on the Iris Benchmark  
> **Protocol Version:** {protocol_version} | **Execution Timestamp:** {timestamp}  
> **Repository Context:** Model Autopsy ML Engine  

---

## 1. Executive Summary

- **Primary Research Question:** *"How does Gaussian input noise affect the Macro-F1 performance of a Random Forest classifier on the Iris dataset?"*
- **Baseline Performance ($s = 0.00$):** Macro-F1 = `{b_f1:.4f}`, Accuracy = `{b_acc:.4f}`
- **Worst-Case Performance ($s = {worst_sev:.2f}$):** Macro-F1 = `{worst_f1:.4f}` (Absolute degradation = `{(b_f1 - worst_f1) * 100:.2f} pp`)
- **Observed Failure Boundary ($s^*$):** {boundary_text}
- **Mandated Boundary Caption:**
  > *"{failure_boundary_result.get('boundary_caption')}"*

---

## 2. Experimental Configuration

| Component | Value / Specification |
|---|---|
| **Dataset** | Fisher Iris Benchmark (150 instances, 4 features, 3 classes) |
| **Train/Test Partitioning** | Stratified 80/20 split (`split_seed = {seeds_config.get('split_seed', 42)}`, Frozen) |
| **Sample Counts** | $N_{{\\text{{train}}}} = 120$ (40/class), $N_{{\\text{{test}}}} = 30$ (10/class) |
| **Feature Standard Deviations ($\sigma_j$)** | Estimated strictly on $X_{{\\text{{train}}}}$ ($ddof=1$) |
| **Model Family** | `RandomForestClassifier` (100 estimators, unconstrained depth, Gini criterion) |
| **Model PRNG Seed** | `model_seed = {seeds_config.get('model_seed', 42)}` |
| **Noise Formulation** | $\\varepsilon_{{ij}} \\sim \\mathcal{{N}}(0, (s \\cdot \\sigma_j)^2)$, where $s \\in [0.00, 0.30]$ |
| **Reliability Criterion** | Strict failure if $\\text{{Macro-F1}} < {failure_threshold:.2f}$ |

---

## 3. Systematic Robustness Degradation Results

| Severity ($s$) | Macro-F1 | Accuracy | Abs Degradation (pp) | Rel Degradation (%) | Status | Rel Drop > 15% Flag |
|---|---|---|---|---|---|---|
{table_block}

*Note: Absolute degradation is reported in percentage points (pp). Relative degradation represents percentage drop relative to baseline Macro-F1.*

---

## 4. Empirical Feature Vulnerability Analysis

Features perturbed independently at $s = 0.20$ to quantify relative empirical sensitivity:

| Rank | Feature Name | Macro-F1 Drop (pp) | Isolated Macro-F1 |
|---|---|---|---|
{feature_table_block}

> **Mandated Sensitivity Caveat:** *"{feature_vulnerabilities[0].get('caveat') if feature_vulnerabilities else 'Empirical sensitivity — not a causal explanation.'}"*

---

## 5. Failure Boundary Characterization

- **Threshold Setting:** $\\text{{Macro-F1}} < {failure_threshold:.2f}$
- **Observed Failure Boundary ($s^*$):** {boundary_text}
- **Diagnostic Finding:** {failure_boundary_result.get('summary_message')}
- **Mandated Reporting Caption:**
  > *"{failure_boundary_result.get('boundary_caption')}"*

---

## 6. Scientific Limitations & Threats to Validity

1. **Test Set Granularity:** With $N_{{\\text{{test}}}} = 30$ samples (10 per class), a single misclassified sample alters accuracy and recall by $3.33\\,\\text{{percentage points}}$.
2. **Benchmark Scale:** The Iris dataset is small, low-dimensional ($D=4$), and possesses well-separated clusters; results do not directly extrapolate to high-dimensional or complex data modalities.
3. **Perturbation Model:** Additive Gaussian noise is a synthetic perturbation that does not represent structured corruptions or adversarial attacks.
4. **Non-Causal Sensitivity:** Feature rankings describe observational sensitivity under this perturbation, not causal mechanisms.

---

## 7. Reproducibility Statement

The development experiment was executed with single-seed isolation (`seed = 42`).  
To deterministically reproduce this exact run:
```bash
python scripts/experiments/run_e001.py --seed 42
```
Full multi-seed statistical evaluation suite ($R=5$ seeds: `[42, 123, 456, 789, 1011]`) is specified for future research extensions.
"""
