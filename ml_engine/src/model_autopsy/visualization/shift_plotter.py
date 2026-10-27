"""Visualization module for Experiment E006: Systematic Distribution Shift (RQ6)."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REGIME_COLORS = {
    "directional_allometric": "#2563eb",  # blue
    "directional_petal_pos": "#dc2626",   # red
    "directional_petal_neg": "#d97706",   # amber
    "dispersion_dilation": "#059669",     # green
    "selection_bias": "#7c3aed",          # purple
}

REGIME_LABELS = {
    "directional_allometric": "Allometric Translation (+all)",
    "directional_petal_pos": "Petal Translation (+petal)",
    "directional_petal_neg": "Petal Inversion (-petal)",
    "dispersion_dilation": "Dispersion Dilation (outward)",
    "selection_bias": "Subpop. Selection (PC1)",
}

REGIME_MARKERS = {
    "directional_allometric": "o",
    "directional_petal_pos": "s",
    "directional_petal_neg": "^",
    "dispersion_dilation": "D",
    "selection_bias": "v",
}


def plot_e006_distribution_shift(
    e006_results: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Path]:
    """Generate publication-grade figures for Experiment E006.

    Generates:
        1. covariate_shift_curves.png: Macro-F1 curves under all shift regimes with 95% CIs and 0.80 failure line.
        2. directional_asymmetry_bars.png: Bar chart comparing positive vs negative petal shift terminal drops.
        3. shift_vs_corruption_comparison.png: Comparison between directional shift and isotropic noise.

    Args:
        e006_results: Complete execution results dictionary from run_e006_experiment.
        output_dir: Target directory where figures will be saved.

    Returns:
        Dictionary mapping figure keys to saved image Path objects.
    """
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    generated_paths: Dict[str, Path] = {}
    models_data = e006_results.get("models", {})
    if not models_data:
        return generated_paths

    model_ids = list(models_data.keys())
    severities = e006_results.get("severities", [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
    shift_regimes = list(REGIME_COLORS.keys())

    # =========================================================================
    # Figure 1: Covariate Shift Curves Across Models (3-panel)
    # =========================================================================
    fig, axes = plt.subplots(1, len(model_ids), figsize=(6 * len(model_ids), 5), sharey=True)
    if len(model_ids) == 1:
        axes = [axes]

    for ax, m_id in zip(axes, model_ids):
        m_data = models_data[m_id]
        m_name = m_data.get("name", m_id.replace("_", " ").title())

        # Failure threshold line
        ax.axhline(0.80, color="#dc2626", linestyle=":", linewidth=1.5, alpha=0.8, label="Failure (0.80)")

        for regime in shift_regimes:
            reg_data = m_data.get("regimes", {}).get(regime)
            if not reg_data:
                continue

            means = reg_data.get("mean_macro_f1", [])
            ci_lows = reg_data.get("ci_lower", [])
            ci_highs = reg_data.get("ci_upper", [])

            if len(means) == len(severities):
                c = REGIME_COLORS.get(regime, "#4b5563")
                lbl = REGIME_LABELS.get(regime, regime)
                marker = REGIME_MARKERS.get(regime, "o")

                ax.plot(severities, means, marker=marker, label=lbl, color=c, linewidth=2, markersize=5)
                if len(ci_lows) == len(severities) and len(ci_highs) == len(severities):
                    ax.fill_between(severities, ci_lows, ci_highs, color=c, alpha=0.15)

        ax.set_title(f"{m_name}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Shift Severity (s)", fontsize=11)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlim(-0.01, max(severities) + 0.01)
        ax.grid(True, linestyle="--", alpha=0.5)

    axes[0].set_ylabel("Macro-Averaged F1-Score", fontsize=11)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=min(len(labels), 6), frameon=True)
    fig.tight_layout()

    fig1_path = figures_dir / "covariate_shift_curves.png"
    fig.savefig(fig1_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    generated_paths["covariate_shift_curves"] = fig1_path

    # =========================================================================
    # Figure 2: Directional Asymmetry Comparison (+petal vs -petal)
    # =========================================================================
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(model_ids))
    width = 0.35

    pos_drops = []
    neg_drops = []
    pos_errs = []
    neg_errs = []

    for m_id in model_ids:
        m_regimes = models_data[m_id].get("regimes", {})
        pos_data = m_regimes.get("directional_petal_pos", {})
        neg_data = m_regimes.get("directional_petal_neg", {})

        pos_drop = pos_data.get("mean_terminal_drop", 0.0)
        neg_drop = neg_data.get("mean_terminal_drop", 0.0)
        pos_sem = pos_data.get("terminal_drop_sem", 0.0)
        neg_sem = neg_data.get("terminal_drop_sem", 0.0)

        pos_drops.append(pos_drop)
        neg_drops.append(neg_drop)
        pos_errs.append(pos_sem)
        neg_errs.append(neg_sem)

    rects1 = ax.bar(x - width / 2, pos_drops, width, yerr=pos_errs, capsize=5, label="+ Petal Translation (Higher Morph)", color="#dc2626", alpha=0.85)
    rects2 = ax.bar(x + width / 2, neg_drops, width, yerr=neg_errs, capsize=5, label="- Petal Translation (Lower Morph)", color="#d97706", alpha=0.85)

    ax.set_ylabel("Terminal Absolute Degradation (pp)", fontsize=11)
    ax.set_title("Directional Shift Asymmetry along Petal Axis (s=0.30)", fontsize=13, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([models_data[m].get("name", m.replace("_", " ").title()) for m in model_ids], fontsize=11)
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    fig2_path = figures_dir / "directional_asymmetry_bars.png"
    fig.savefig(fig2_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    generated_paths["directional_asymmetry_bars"] = fig2_path

    # =========================================================================
    # Figure 3: Shift vs Localized Corruption Comparison
    # =========================================================================
    fig, axes = plt.subplots(1, len(model_ids), figsize=(6 * len(model_ids), 5), sharey=True)
    if len(model_ids) == 1:
        axes = [axes]

    for ax, m_id in zip(axes, model_ids):
        m_data = models_data[m_id]
        m_name = m_data.get("name", m_id.replace("_", " ").title())

        ax.axhline(0.80, color="#dc2626", linestyle=":", linewidth=1.5, alpha=0.8, label="Failure (0.80)")

        # Directional shift curve (e.g. petal_pos)
        petal_pos = m_data.get("regimes", {}).get("directional_petal_pos", {})
        shift_f1 = petal_pos.get("mean_macro_f1", [])
        if len(shift_f1) == len(severities):
            ax.plot(severities, shift_f1, "r-o", linewidth=2, label="Systematic Shift (+petal)")

        # Gaussian noise curve (simulated/benchmark)
        noise_f1 = m_data.get("benchmark_noise_macro_f1", [])
        if len(noise_f1) == len(severities):
            ax.plot(severities, noise_f1, "b--s", linewidth=2, label="Stochastic Noise (E001/E002)")

        ax.set_title(f"{m_name}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Severity (s)", fontsize=11)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlim(-0.01, max(severities) + 0.01)
        ax.grid(True, linestyle="--", alpha=0.5)

    axes[0].set_ylabel("Macro-Averaged F1-Score", fontsize=11)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=len(labels), frameon=True)
    fig.tight_layout()

    fig3_path = figures_dir / "shift_vs_corruption_comparison.png"
    fig.savefig(fig3_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    generated_paths["shift_vs_corruption_comparison"] = fig3_path

    return generated_paths
