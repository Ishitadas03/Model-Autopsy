"""Visualization module for E005 Feature Vulnerability Analysis (RQ3)."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


FEATURE_COLORS = [
    "#2563eb",  # blue: sepal length
    "#059669",  # green: sepal width
    "#d97706",  # amber: petal length
    "#dc2626",  # red: petal width
]

FEATURE_STYLES = ["-", "--", "-.", ":"]
FEATURE_MARKERS = ["o", "s", "^", "D"]


def plot_e005_feature_vulnerability(
    e005_results: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Path]:
    """Generate publication-grade figures for Experiment E005.

    Generates:
        1. feature_degradation_curves.png: Macro-F1 degradation curves across severities for each feature.
        2. feature_vulnerability_bars.png: Bar chart of terminal degradation at s=0.30 with 95% CIs.
        3. clean_vs_vulnerability_scatter.png: Clean baseline importance vs stress degradation.

    Args:
        e005_results: Complete execution results dictionary from run_e005_experiment.
        output_dir: Target directory where figures will be saved.

    Returns:
        Dictionary mapping figure keys to saved image Path objects.
    """
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    generated_paths: Dict[str, Path] = {}

    models_data = e005_results.get("models", {})
    if not models_data:
        return generated_paths

    model_ids = list(models_data.keys())
    feature_names = e005_results.get("feature_names", [
        "sepal length (cm)", "sepal width (cm)", "petal length (cm)", "petal width (cm)"
    ])
    severities = e005_results.get("severities", [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
    primary_operator = e005_results.get("primary_operator", "single_feature_gaussian_noise")

    # =========================================================================
    # Figure 1: Feature Degradation Curves across Models (3-panel)
    # =========================================================================
    fig, axes = plt.subplots(1, len(model_ids), figsize=(6 * len(model_ids), 5), sharey=True)
    if len(model_ids) == 1:
        axes = [axes]

    for ax, m_id in zip(axes, model_ids):
        m_data = models_data[m_id].get("operators", {}).get(primary_operator, {})
        features_dict = m_data.get("features", {})

        for j, (f_name, f_color, f_style, f_marker) in enumerate(zip(
            feature_names, FEATURE_COLORS, FEATURE_STYLES, FEATURE_MARKERS
        )):
            f_stats = features_dict.get(f_name, {}).get("severity_aggregates", [])
            if not f_stats:
                continue

            sevs = [s["severity"] for s in f_stats]
            delta_means = [s["delta_abs_mean"] for s in f_stats]
            ci_lows = [s["delta_abs_ci95_low"] for s in f_stats]
            ci_highs = [s["delta_abs_ci95_high"] for s in f_stats]

            ax.plot(
                sevs,
                delta_means,
                label=f_name,
                color=f_color,
                linestyle=f_style,
                marker=f_marker,
                linewidth=2.0,
                markersize=6,
            )
            ax.fill_between(sevs, ci_lows, ci_highs, color=f_color, alpha=0.15)

        clean_baseline = models_data[m_id].get("clean_macro_f1_mean", 0.95)
        # Failure threshold line in delta coordinates: delta = clean_baseline - 0.80
        crit_delta = max(0.0, clean_baseline - 0.80)
        ax.axhline(
            crit_delta,
            color="#ef4444",
            linestyle=":",
            alpha=0.7,
            label=f"Failure Threshold ({crit_delta:.2f} pp drop)" if ax == axes[0] else None,
        )

        model_title = m_id.replace("_", " ").title()
        ax.set_title(f"{model_title}\n(Clean Macro-F1 = {clean_baseline:.4f})", fontsize=12, fontweight="bold")
        ax.set_xlabel("Perturbation Severity ($s$)", fontsize=11)
        ax.set_xlim(-0.01, max(severities) + 0.01)
        ax.grid(True, linestyle="--", alpha=0.5)

    axes[0].set_ylabel("Absolute Macro-F1 Degradation $\\Delta_{\\text{abs}}$ (pp)", fontsize=11)
    axes[0].legend(loc="upper left", fontsize=9, framealpha=0.9)

    plt.suptitle(
        f"E005: Feature-Level Degradation Trajectories under {primary_operator.replace('_', ' ').title()}\n"
        "(Error bands: Student's t 95% Confidence Intervals across 5 seeds)",
        fontsize=13,
        fontweight="bold",
        y=1.03,
    )
    plt.tight_layout()
    curve_path = figures_dir / "feature_degradation_curves.png"
    plt.savefig(curve_path, dpi=300, bbox_inches="tight")
    plt.close()
    generated_paths["feature_degradation_curves"] = curve_path

    # =========================================================================
    # Figure 2: Terminal Vulnerability Bar Chart with 95% CI Error Bars
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 6))
    n_features = len(feature_names)
    n_models = len(model_ids)
    bar_width = 0.8 / n_models

    x_indices = np.arange(n_features)

    for i, m_id in enumerate(model_ids):
        m_data = models_data[m_id].get("operators", {}).get(primary_operator, {})
        features_dict = m_data.get("features", {})

        terminal_means = []
        terminal_errors = []

        for f_name in feature_names:
            f_stats = features_dict.get(f_name, {}).get("severity_aggregates", [])
            # Terminal severity is s = 0.30
            term_stat = f_stats[-1] if f_stats else {}
            mean_val = term_stat.get("delta_abs_mean", 0.0)
            ci_high = term_stat.get("delta_abs_ci95_high", mean_val)
            err = max(0.0, ci_high - mean_val)

            terminal_means.append(mean_val)
            terminal_errors.append(err)

        positions = x_indices + (i - n_models / 2.0 + 0.5) * bar_width
        ax.bar(
            positions,
            terminal_means,
            bar_width,
            yerr=terminal_errors,
            capsize=4,
            label=m_id.replace("_", " ").title(),
            alpha=0.85,
        )

    ax.set_title(
        f"E005: Terminal Feature Vulnerability at s=0.30 ({primary_operator.replace('_', ' ').title()})\n"
        "Error bars represent 95% Student's t Confidence Intervals",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xticks(x_indices)
    ax.set_xticklabels(feature_names, fontsize=10, rotation=15)
    ax.set_ylabel("Macro-F1 Degradation $\\Delta_{\\text{abs}}$ at $s=0.30$ (pp)", fontsize=11)
    ax.legend(title="Model Architecture", fontsize=10)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    bar_path = figures_dir / "feature_vulnerability_bars.png"
    plt.savefig(bar_path, dpi=300, bbox_inches="tight")
    plt.close()
    generated_paths["feature_vulnerability_bars"] = bar_path

    # =========================================================================
    # Figure 3: Clean Baseline Importance vs Stress Degradation Scatter Plot
    # =========================================================================
    fig, ax = plt.subplots(figsize=(8, 6))

    scatter_markers = ["o", "s", "^"]
    for m_idx, m_id in enumerate(model_ids):
        m_obj = models_data[m_id]
        clean_importances = m_obj.get("clean_feature_importance", {})
        m_data = m_obj.get("operators", {}).get(primary_operator, {})
        features_dict = m_data.get("features", {})

        x_vals = []
        y_vals = []
        labels = []

        for f_name in feature_names:
            c_imp = clean_importances.get(f_name, 0.0)
            f_stats = features_dict.get(f_name, {}).get("severity_aggregates", [])
            term_val = f_stats[-1].get("delta_abs_mean", 0.0) if f_stats else 0.0

            x_vals.append(c_imp)
            y_vals.append(term_val)
            labels.append(f_name.split(" ")[0])  # Short label

        marker = scatter_markers[m_idx % len(scatter_markers)]
        ax.scatter(
            x_vals,
            y_vals,
            s=120,
            marker=marker,
            label=m_id.replace("_", " ").title(),
            alpha=0.85,
        )

        for x, y, lab in zip(x_vals, y_vals, labels):
            ax.annotate(
                lab,
                (x, y),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
                alpha=0.8,
            )

    ax.set_title(
        "E005: Clean Feature Importance vs. Stress Vulnerability (H3)\n"
        "Testing Decoupling Between Nominal Importance and Perturbation Fragility",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Normalized Clean Feature Importance", fontsize=11)
    ax.set_ylabel("Terminal Degradation $\\Delta_{\\text{abs}}$ at $s=0.30$ (pp)", fontsize=11)
    ax.legend(title="Model", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    scatter_path = figures_dir / "clean_vs_vulnerability_scatter.png"
    plt.savefig(scatter_path, dpi=300, bbox_inches="tight")
    plt.close()
    generated_paths["clean_vs_vulnerability_scatter"] = scatter_path

    return generated_paths
