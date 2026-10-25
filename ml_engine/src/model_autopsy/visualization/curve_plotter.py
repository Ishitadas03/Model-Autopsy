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
