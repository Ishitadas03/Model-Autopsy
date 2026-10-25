"""Visualization module for E004 failure pattern analysis."""

from pathlib import Path
from typing import Any, Dict, List
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np


def plot_e004_failure_patterns(
    summary_data: Dict[str, Any],
    X_test_2d: np.ndarray,
    y_test: np.ndarray,
    output_path: Path,
) -> Path:
    """Generate 4-panel publication-quality failure pattern analysis figure.

    Panels:
        (A) Class-wise error rate trajectories across severities.
        (B) Error persistence ratio distribution & first-error severity.
        (C) Inter-model Jaccard error set similarity matrix across severities.
        (D) 2D PCA feature-space projection depicting consensus vs model-unique errors.

    Args:
        summary_data: Quantitative synthesis from failure_patterns analysis.
        X_test_2d: 2D PCA projection of clean test instances.
        y_test: Ground truth test labels.
        output_path: Destination path for PNG plot.

    Returns:
        Path to saved PNG plot.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(15, 11), dpi=300)
    fig.patch.set_facecolor("#070709")

    # Dark-mode styling for all subplots
    for ax in axes.flat:
        ax.set_facecolor("#0D0E12")
        ax.grid(True, linestyle="--", linewidth=0.6, color="#232733", alpha=0.8, zorder=1)
        ax.tick_params(colors="#A0A5B5", labelsize=9)
        for spine in ax.spines.values():
            spine.set_color("#232733")

    # =========================================================================
    # Panel A: Class-Wise Error Rate Trajectories
    # =========================================================================
    ax_a = axes[0, 0]
    severities = summary_data["protocol"]["severities"]
    class_trajectories = summary_data["class_vulnerabilities"]["trajectories"]

    colors_class = {"setosa": "#00E5FF", "versicolor": "#FFB300", "virginica": "#E040FB"}
    markers_class = {"setosa": "o", "versicolor": "s", "virginica": "^"}

    for c_name, rates in class_trajectories.items():
        ax_a.plot(
            severities,
            rates,
            marker=markers_class.get(c_name, "o"),
            color=colors_class.get(c_name, "#FFFFFF"),
            linewidth=2.2,
            label=f"Iris {c_name.capitalize()} (n=10)",
            zorder=4,
        )

    ax_a.set_title(
        "(A) Class Vulnerability Asymmetry (Macro Error Rate by Class)",
        color="#FFFFFF",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    ax_a.set_xlabel("Severity Parameter (s)", color="#A0A5B5", fontsize=9.5)
    ax_a.set_ylabel("Class Error Rate (CER)", color="#A0A5B5", fontsize=9.5)
    ax_a.set_ylim(-0.05, 1.05)
    ax_a.legend(
        facecolor="#161822",
        edgecolor="#2E3346",
        labelcolor="#FFFFFF",
        fontsize=8.5,
        loc="upper left",
    )

    # =========================================================================
    # Panel B: Error Persistence Ratio Distribution
    # =========================================================================
    ax_b = axes[0, 1]
    eprs = summary_data["error_persistence"]["valid_eprs"]
    if len(eprs) > 0:
        counts, bins, patches = ax_b.hist(
            eprs,
            bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.01],
            color="#00E5FF",
            edgecolor="#070709",
            alpha=0.85,
            zorder=3,
            rwidth=0.85,
        )
        for patch in patches:
            patch.set_facecolor("#00E5FF")
    ax_b.set_title(
        "(B) Error Persistence Ratio (EPR) Distribution Under Nested Filtration",
        color="#FFFFFF",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    ax_b.set_xlabel("Error Persistence Ratio (1.0 = Absorbing Error State)", color="#A0A5B5", fontsize=9.5)
    ax_b.set_ylabel("Number of Instances", color="#A0A5B5", fontsize=9.5)
    mean_epr = summary_data["error_persistence"]["mean_epr"]
    if mean_epr is not None:
        ax_b.axvline(
            mean_epr,
            color="#FF4D2D",
            linestyle="--",
            linewidth=1.8,
            label=f"Mean EPR = {mean_epr:.2f}",
            zorder=5,
        )
        ax_b.legend(
            facecolor="#161822",
            edgecolor="#2E3346",
            labelcolor="#FFFFFF",
            fontsize=8.5,
        )

    # =========================================================================
    # Panel C: Inter-Model Jaccard Error-Set Similarity Trajectories
    # =========================================================================
    ax_c = axes[1, 0]
    jaccard_series = summary_data["inter_model_concordance"]["jaccard_trajectories"]

    pair_colors = {
        "rf_vs_lr": "#00E5FF",
        "rf_vs_gb": "#E040FB",
        "lr_vs_gb": "#FFB300",
    }
    pair_labels = {
        "rf_vs_lr": "Random Forest vs Logistic Regression",
        "rf_vs_gb": "Random Forest vs Gradient Boosting",
        "lr_vs_gb": "Logistic Regression vs Gradient Boosting",
    }

    for pair_key, j_vals in jaccard_series.items():
        ax_c.plot(
            severities,
            j_vals,
            marker="o",
            color=pair_colors.get(pair_key, "#FFFFFF"),
            linewidth=2.0,
            label=pair_labels.get(pair_key, pair_key),
            zorder=4,
        )

    ax_c.set_title(
        "(C) Inter-Model Error-Set Concordance (Jaccard Index across Severities)",
        color="#FFFFFF",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    ax_c.set_xlabel("Severity Parameter (s)", color="#A0A5B5", fontsize=9.5)
    ax_c.set_ylabel("Jaccard Similarity Index", color="#A0A5B5", fontsize=9.5)
    ax_c.set_ylim(-0.05, 1.05)
    ax_c.legend(
        facecolor="#161822",
        edgecolor="#2E3346",
        labelcolor="#FFFFFF",
        fontsize=8.5,
        loc="lower left",
    )

    # =========================================================================
    # Panel D: 2D Feature-Space Projection & Failure Localization
    # =========================================================================
    ax_d = axes[1, 1]
    consensus_idx = set(summary_data["inter_model_concordance"]["worst_case_consensus_indices"])
    rf_only = set(summary_data["inter_model_concordance"]["rf_unique_indices"])
    lr_only = set(summary_data["inter_model_concordance"]["lr_unique_indices"])
    gb_only = set(summary_data["inter_model_concordance"]["gb_unique_indices"])

    # Base test samples by class
    for k, c_name in enumerate(["setosa", "versicolor", "virginica"]):
        mask = y_test == k
        ax_d.scatter(
            X_test_2d[mask, 0],
            X_test_2d[mask, 1],
            color=colors_class[c_name],
            alpha=0.35,
            s=45,
            edgecolors="none",
            label=f"Class: {c_name.capitalize()}",
            zorder=2,
        )

    # Highlight consensus failures
    if consensus_idx:
        c_arr = list(consensus_idx)
        ax_d.scatter(
            X_test_2d[c_arr, 0],
            X_test_2d[c_arr, 1],
            color="#FF4D2D",
            marker="X",
            s=120,
            linewidth=1.5,
            edgecolors="#FFFFFF",
            label="Consensus Failures (All Models)",
            zorder=6,
        )

    # Highlight model-unique failures
    unique_any = list(rf_only.union(lr_only).union(gb_only))
    if unique_any:
        ax_d.scatter(
            X_test_2d[unique_any, 0],
            X_test_2d[unique_any, 1],
            color="#FFE600",
            marker="D",
            s=70,
            linewidth=1.2,
            edgecolors="#000000",
            label="Model-Unique Failures",
            zorder=5,
        )

    ax_d.set_title(
        "(D) Feature-Space Decision Margin & Failure Localization (PCA)",
        color="#FFFFFF",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )
    ax_d.set_xlabel("Principal Component 1 (PC1)", color="#A0A5B5", fontsize=9.5)
    ax_d.set_ylabel("Principal Component 2 (PC2)", color="#A0A5B5", fontsize=9.5)
    ax_d.legend(
        facecolor="#161822",
        edgecolor="#2E3346",
        labelcolor="#FFFFFF",
        fontsize=8.0,
        loc="upper right",
    )

    # =========================================================================
    # Header & Mandatory Captions
    # =========================================================================
    fig.suptitle(
        "Experiment E004: Multi-Model Empirical Failure Pattern Analysis (RQ7)\n"
        "Fisher Iris Benchmark (N_train=120, N_test=30) — 5 Research Seeds",
        color="#FFFFFF",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )

    # Captions at bottom
    fig.text(
        0.5,
        0.015,
        "Observed failure boundary under the specified experimental configuration.  |  "
        "Empirical sensitivity — not a causal explanation.  |  Sample size N_test=30 (n_k=10/class).",
        ha="center",
        va="center",
        color="#8B92A4",
        fontsize=8.5,
        fontstyle="italic",
    )

    plt.tight_layout(rect=[0.02, 0.04, 0.98, 0.94])
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

    return output_path
