"""Robustness curve visualization module for Model Autopsy."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt


def plot_robustness_curve(
    severity_records: List[Dict[str, Any]],
    output_path: Path,
    failure_threshold: float = 0.80,
    experiment_id: str = "E001",
    model_name: str = "Random Forest Classifier",
    dataset_name: str = "Iris Flower Dataset",
) -> Path:
    """Plot publication-quality robustness curve for experiment results.

    Args:
        severity_records: List of records containing 'severity', 'macro_f1', and 'accuracy'.
        output_path: Destination file path for PNG artifact.
        failure_threshold: Predefined reliability threshold (default 0.80).
        experiment_id: Experiment identifier for title and annotations.
        model_name: Name of evaluated model.
        dataset_name: Name of evaluated dataset.

    Returns:
        Path to the saved PNG plot.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    severities = [float(r["severity"]) for r in severity_records]
    macro_f1s = [float(r["macro_f1"]) for r in severity_records]
    accuracies = [float(r["accuracy"]) for r in severity_records]

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)

    # Dark-mode inspired scientific palette
    ax.set_facecolor("#0D0E12")
    fig.patch.set_facecolor("#070709")

    # Grid
    ax.grid(True, linestyle="--", linewidth=0.6, color="#232733", alpha=0.8, zorder=1)

    # Shaded failure regime below threshold
    min_x, max_x = min(severities), max(severities)
    x_pad = (max_x - min_x) * 0.04 if max_x > min_x else 0.01
    ax.axhspan(0.0, failure_threshold, facecolor="#FF4D2D", alpha=0.10, zorder=2, label="Failure Regime (< 0.80)")

    # Failure threshold horizontal dashed line
    ax.axhline(
        y=failure_threshold,
        color="#FF4D2D",
        linestyle="--",
        linewidth=1.4,
        alpha=0.9,
        zorder=3,
        label=f"Failure Threshold ({failure_threshold:.2f})",
    )

    # Primary Curve: Macro-F1
    ax.plot(
        severities,
        macro_f1s,
        color="#38BDF8",  # Electric sky blue
        marker="o",
        markersize=7,
        linewidth=2.2,
        zorder=4,
        label="Macro-F1 (Primary)",
    )

    # Secondary Curve: Accuracy
    ax.plot(
        severities,
        accuracies,
        color="#A78BFA",  # Violet
        marker="s",
        markersize=5,
        linewidth=1.6,
        linestyle=":",
        alpha=0.85,
        zorder=4,
        label="Accuracy (Secondary)",
    )

    # Annotate points
    for s, f1 in zip(severities, macro_f1s):
        ax.annotate(
            f"{f1:.3f}",
            (s, f1),
            textcoords="offset points",
            xytext=(0, 9),
            ha="center",
            fontsize=8.5,
            color="#E2E8F0",
            fontfamily="monospace",
            zorder=5,
        )

    # Axes limits and labels
    ax.set_xlim(min_x - x_pad, max_x + x_pad)
    ax.set_ylim(0.50, 1.05)

    ax.set_xlabel("Gaussian Noise Severity ($s$)", fontsize=11, fontweight="semibold", color="#F1F5F9", labelpad=8)
    ax.set_ylabel("Evaluation Score", fontsize=11, fontweight="semibold", color="#F1F5F9", labelpad=8)
    ax.set_title(
        f"Robustness Degradation Trajectory — {experiment_id}\n"
        f"Model: {model_name} | Dataset: {dataset_name}",
        fontsize=12,
        fontweight="bold",
        color="#F8FAFC",
        pad=12,
    )

    # Tick parameters
    ax.tick_params(colors="#94A3B8", labelsize=9.5)
    for spine in ax.spines.values():
        spine.set_color("#334155")
        spine.set_linewidth(0.8)

    # Legend
    legend = ax.legend(
        loc="lower left",
        facecolor="#111318",
        edgecolor="#334155",
        fontsize=9,
        labelcolor="#E2E8F0",
    )
    legend.get_frame().set_alpha(0.9)

    # Subtitle / scientific caption at bottom
    fig.text(
        0.5,
        0.015,
        "Observed failure boundary under the specified experimental configuration.",
        ha="center",
        fontsize=8.5,
        fontstyle="italic",
        color="#64748B",
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

    return output_path


def plot_multiseed_robustness_curve(
    severity_aggregates: List[Any],
    output_path: Path,
    per_seed_runs: Optional[Dict[int, Dict[str, Any]]] = None,
    failure_threshold: float = 0.80,
    experiment_id: str = "E001",
    model_name: str = "Random Forest (R=5 Seeds)",
    dataset_name: str = "Iris Flower Dataset",
) -> Path:
    """Plot publication-grade multi-seed robustness curve with 95% Student's t CI band.

    Args:
        severity_aggregates: List of SeverityAggregateStatistics objects or dictionaries.
        output_path: Destination path for PNG artifact.
        per_seed_runs: Optional dictionary of individual seed run results for dispersion lines.
        failure_threshold: Reliability threshold line (default 0.80).
        experiment_id: Experiment ID for title.
        model_name: Model descriptor.
        dataset_name: Dataset descriptor.

    Returns:
        Path to the saved PNG plot.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    severities = []
    mean_f1s = []
    ci_lowers = []
    ci_uppers = []
    mean_accs = []

    for agg in severity_aggregates:
        if hasattr(agg, "severity"):
            sev = float(agg.severity)
            m_f1 = float(agg.macro_f1.mean)
            low = float(agg.macro_f1.ci_lower)
            high = float(agg.macro_f1.ci_upper)
            m_acc = float(agg.accuracy.mean)
        else:
            sev = float(agg["severity"])
            m_f1 = float(agg["macro_f1"]["mean"])
            low = float(agg["macro_f1"]["ci_lower"])
            high = float(agg["macro_f1"]["ci_upper"])
            m_acc = float(agg["accuracy"]["mean"])

        severities.append(sev)
        mean_f1s.append(m_f1)
        ci_lowers.append(low)
        ci_uppers.append(high)
        mean_accs.append(m_acc)

    fig, ax = plt.subplots(figsize=(9.5, 6.0), dpi=300)

    # Dark-mode styling
    ax.set_facecolor("#0D0E12")
    fig.patch.set_facecolor("#070709")

    # Grid
    ax.grid(True, linestyle="--", linewidth=0.6, color="#232733", alpha=0.8, zorder=1)

    # Shaded failure regime below threshold
    min_x, max_x = min(severities), max(severities)
    x_pad = (max_x - min_x) * 0.04 if max_x > min_x else 0.01
    ax.axhspan(0.0, failure_threshold, facecolor="#FF4D2D", alpha=0.10, zorder=2, label="Failure Regime (< 0.80)")

    # Failure threshold horizontal dashed line
    ax.axhline(
        y=failure_threshold,
        color="#FF4D2D",
        linestyle="--",
        linewidth=1.4,
        alpha=0.9,
        zorder=3,
        label=f"Failure Threshold ({failure_threshold:.2f})",
    )

    # Shaded 95% Student's t CI band for Macro-F1
    ax.fill_between(
        severities,
        ci_lowers,
        ci_uppers,
        color="#38BDF8",
        alpha=0.22,
        zorder=4,
        label="Mean Macro-F1 95% CI (Student's t, df=4)",
    )

    # Individual seed trajectories if provided
    if per_seed_runs:
        for seed_val, s_data in per_seed_runs.items():
            s_recs = s_data.get("severity_records", [])
            s_sevs = [float(r["severity"]) for r in s_recs]
            s_f1s = [float(r["macro_f1"]) for r in s_recs]
            ax.plot(
                s_sevs,
                s_f1s,
                color="#64748B",
                linestyle="--",
                linewidth=0.9,
                alpha=0.45,
                zorder=4,
            )
        # Dummy line for legend
        ax.plot([], [], color="#64748B", linestyle="--", linewidth=0.9, alpha=0.6, label="Individual Seed Runs (R=5)")

    # Primary Curve: Mean Macro-F1
    ax.plot(
        severities,
        mean_f1s,
        color="#38BDF8",  # Electric sky blue
        marker="o",
        markersize=7,
        linewidth=2.4,
        zorder=5,
        label="Mean Macro-F1 (Primary)",
    )

    # Secondary Curve: Mean Accuracy
    ax.plot(
        severities,
        mean_accs,
        color="#A78BFA",  # Violet
        marker="s",
        markersize=5,
        linewidth=1.6,
        linestyle=":",
        alpha=0.85,
        zorder=5,
        label="Mean Accuracy (Secondary)",
    )

    # Annotate mean Macro-F1 points
    for s, m, low, high in zip(severities, mean_f1s, ci_lowers, ci_uppers):
        ax.annotate(
            f"{m:.3f}\n[±{(high - low)/2:.3f}]",
            (s, m),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8,
            color="#E2E8F0",
            fontfamily="monospace",
            zorder=6,
        )

    ax.set_xlim(min_x - x_pad, max_x + x_pad)
    ax.set_ylim(0.50, 1.05)

    ax.set_xlabel("Gaussian Noise Severity ($s$)", fontsize=11, fontweight="semibold", color="#F1F5F9", labelpad=8)
    ax.set_ylabel("Evaluation Metric Score", fontsize=11, fontweight="semibold", color="#F1F5F9", labelpad=8)
    ax.set_title(
        f"Multi-Seed Robustness Degradation Trajectory (R=5 Seeds) — {experiment_id}\n"
        f"Model: {model_name} | Dataset: {dataset_name}",
        fontsize=12,
        fontweight="bold",
        color="#F8FAFC",
        pad=12,
    )

    ax.tick_params(colors="#94A3B8", labelsize=9.5)
    for spine in ax.spines.values():
        spine.set_color("#334155")
        spine.set_linewidth(0.8)

    legend = ax.legend(
        loc="lower left",
        facecolor="#111318",
        edgecolor="#334155",
        fontsize=8.5,
        labelcolor="#E2E8F0",
    )
    legend.get_frame().set_alpha(0.92)

    fig.text(
        0.5,
        0.015,
        "Observed failure boundary under the specified experimental configuration.",
        ha="center",
        fontsize=8.5,
        fontstyle="italic",
        color="#64748B",
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

    return output_path


def plot_e002_multicorruption_comparison(
    corruption_aggregates: Dict[str, List[Dict[str, Any]]],
    output_path: Path,
    failure_threshold: float = 0.80,
    experiment_id: str = "E002",
    model_name: str = "Random Forest Classifier",
    dataset_name: str = "Iris Flower Dataset",
) -> Path:
    """Plot multi-corruption robustness comparison with 95% Student's t CI bands for E002.

    Args:
        corruption_aggregates: Dictionary mapping corruption display label to list of
                               aggregate records (each with 'severity', 'macro_f1_mean',
                               'macro_f1_ci_lower', 'macro_f1_ci_upper').
        output_path: Destination PNG file path.
        failure_threshold: Predefined reliability threshold (default 0.80).
        experiment_id: Experiment identifier for title.
        model_name: Name of evaluated model.
        dataset_name: Name of evaluated dataset.

    Returns:
        Path to the saved PNG plot.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6.0), dpi=300)

    # Dark-mode scientific canvas
    ax.set_facecolor("#0D0E12")
    fig.patch.set_facecolor("#070709")

    # Grid
    ax.grid(True, linestyle="--", linewidth=0.6, color="#232733", alpha=0.8, zorder=1)

    # Style mapping for each corruption modality
    palette = [
        {"color": "#00E5FF", "marker": "o", "label_prefix": "Gaussian Noise"},
        {"color": "#FFB300", "marker": "s", "label_prefix": "MCAR Missingness (Imputed)"},
        {"color": "#E040FB", "marker": "^", "label_prefix": "Outlier Contamination (5σ)"},
    ]

    all_severities = []

    # Plot each corruption's mean curve and confidence band
    for idx, (corr_name, records) in enumerate(corruption_aggregates.items()):
        style = palette[idx % len(palette)]
        severities = [float(r["severity"]) for r in records]
        all_severities.extend(severities)
        means = [float(r["macro_f1_mean"]) for r in records]
        ci_lowers = [float(r["macro_f1_ci_lower"]) for r in records]
        ci_uppers = [float(r["macro_f1_ci_upper"]) for r in records]

        # Shaded 95% CI band
        ax.fill_between(
            severities,
            ci_lowers,
            ci_uppers,
            color=style["color"],
            alpha=0.15,
            zorder=3,
            label=f"{corr_name} 95% CI (t, df=4)",
        )

        # Mean trajectory
        ax.plot(
            severities,
            means,
            color=style["color"],
            marker=style["marker"],
            markersize=6,
            linewidth=2.2,
            zorder=4,
            label=f"{corr_name} Mean",
        )

    min_x, max_x = min(all_severities), max(all_severities)
    x_pad = (max_x - min_x) * 0.04 if max_x > min_x else 0.01

    # Failure regime and threshold
    ax.axhspan(0.0, failure_threshold, facecolor="#FF4D2D", alpha=0.10, zorder=2, label="Failure Regime (< 0.80)")
    ax.axhline(
        y=failure_threshold,
        color="#FF4D2D",
        linestyle="--",
        linewidth=1.4,
        alpha=0.9,
        zorder=2,
        label=f"Failure Threshold ({failure_threshold:.2f})",
    )

    ax.set_xlim(min_x - x_pad, max_x + x_pad)
    ax.set_ylim(0.50, 1.05)

    ax.set_xlabel("Nominal Corruption Severity ($s$)", fontsize=11, fontweight="semibold", color="#F1F5F9", labelpad=8)
    ax.set_ylabel("Macro-F1 Score", fontsize=11, fontweight="semibold", color="#F1F5F9", labelpad=8)
    ax.set_title(
        f"Cross-Corruption Robustness Comparison (RQ2: R=5 Seeds, 95% Student's t CI) — {experiment_id}\n"
        f"Model: {model_name} | Dataset: {dataset_name}",
        fontsize=12,
        fontweight="bold",
        color="#F8FAFC",
        pad=12,
    )

    ax.tick_params(colors="#94A3B8", labelsize=9.5)
    for spine in ax.spines.values():
        spine.set_color("#334155")
        spine.set_linewidth(0.8)

    legend = ax.legend(
        loc="lower left",
        facecolor="#111318",
        edgecolor="#334155",
        fontsize=8.0,
        labelcolor="#E2E8F0",
        ncol=2,
    )
    legend.get_frame().set_alpha(0.92)

    fig.text(
        0.5,
        0.015,
        "Observed failure boundary under the specified experimental configuration.",
        ha="center",
        fontsize=8.5,
        fontstyle="italic",
        color="#64748B",
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)

    return output_path


