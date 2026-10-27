"""Distribution shift analysis, statistical comparisons, and boundary characterization for E006."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.stats as stats


def calculate_audc(severities: List[float], degradations: List[float]) -> float:
    """Calculate Area Under the Degradation Curve (AUDC) using the trapezoidal rule.

    AUDC = sum_{k=1}^{|S|-1} ((Delta_{k-1} + Delta_k) / 2) * (s_k - s_{k-1})

    Args:
        severities: Monotonically increasing list of severity scalars.
        degradations: Absolute degradation values (pp or ratio) at each severity.

    Returns:
        Float AUDC value rounded to 4 decimal places.
    """
    if len(severities) != len(degradations):
        raise ValueError(
            f"Length mismatch: {len(severities)} severities vs {len(degradations)} degradations"
        )
    if len(severities) < 2:
        return 0.0

    s_arr = np.asarray(severities, dtype=np.float64)
    d_arr = np.asarray(degradations, dtype=np.float64)

    # Use np.trapezoid if available (NumPy >= 2.0.0), else fallback to np.trapz
    trap_fn = getattr(np, "trapezoid", getattr(np, "trapz", None))
    if trap_fn is None:
        # Pure manual calculation fallback
        val = float(np.sum(0.5 * (d_arr[:-1] + d_arr[1:]) * np.diff(s_arr)))
    else:
        val = float(trap_fn(d_arr, s_arr))

    return round(float(val), 4)


def find_failure_boundary(
    severities: List[float],
    macro_f1s: List[float],
    threshold: float = 0.80,
) -> Optional[float]:
    """Find the empirical failure boundary s* = min { s in S | Macro-F1(s) < threshold }.

    Args:
        severities: Sorted severity levels.
        macro_f1s: Observed Macro-F1 at each severity level.
        threshold: Reliability threshold (default 0.80).

    Returns:
        The first severity level where Macro-F1 < threshold, or None if the model never fails.
    """
    for s, f1 in zip(severities, macro_f1s):
        if f1 < threshold:
            return float(s)
    return None


def compute_friedman_test(model_degradations: Dict[str, List[float]]) -> Dict[str, Any]:
    """Perform non-parametric omnibus Friedman test across model architectures paired by seed.

    H0: mu_Delta(RF) = mu_Delta(LR) = mu_Delta(GB)
    H1: At least one architecture differs.

    Args:
        model_degradations: Dictionary mapping model names to lists of degradations across matched seeds.

    Returns:
        Dictionary with test statistic, p-value, df, and null rejection flag.
    """
    model_names = list(model_degradations.keys())
    if len(model_names) < 3:
        raise ValueError(f"Friedman test requires at least 3 models, got {len(model_names)}")

    groups = [model_degradations[m] for m in model_names]
    n_seeds = len(groups[0])
    for g in groups[1:]:
        if len(g) != n_seeds:
            raise ValueError("All model groups must have identical sample size (paired by seed)")

    stat, p_value = stats.friedmanchisquare(*groups)
    stat = float(stat)
    p_value = float(p_value)

    return {
        "test": "Friedman Omnibus Test",
        "statistic": round(stat, 4),
        "p_value": round(p_value, 6),
        "degrees_of_freedom": len(model_names) - 1,
        "n_seeds": n_seeds,
        "null_rejected": bool(p_value < 0.05),
    }


def compute_pairwise_model_tests(
    model_degradations: Dict[str, List[float]],
    q_threshold: float = 0.05,
) -> List[Dict[str, Any]]:
    """Compute pairwise paired tests between models with Benjamini-Hochberg FDR correction.

    Args:
        model_degradations: Mapping of model names to degradation vectors across seeds.
        q_threshold: FDR significance threshold (default: 0.05).

    Returns:
        List of pairwise comparison records with unadjusted p-values and BH-adjusted p-values.
    """
    model_names = list(model_degradations.keys())
    raw_comparisons: List[Dict[str, Any]] = []

    for i in range(len(model_names)):
        for j in range(i + 1, len(model_names)):
            m1 = model_names[i]
            m2 = model_names[j]
            v1 = np.asarray(model_degradations[m1], dtype=np.float64)
            v2 = np.asarray(model_degradations[m2], dtype=np.float64)
            diff = v1 - v2
            mean_diff = float(np.mean(diff))

            if np.allclose(diff, 0.0):
                t_stat = 0.0
                p_val = 1.0
            else:
                t_res = stats.ttest_rel(v1, v2)
                t_stat = float(t_res.statistic)
                p_val = float(t_res.pvalue)

            raw_comparisons.append({
                "model_1": m1,
                "model_2": m2,
                "mean_diff": round(mean_diff, 4),
                "t_statistic": round(t_stat, 4),
                "raw_p_value": float(p_val),
            })

    # Benjamini-Hochberg FDR correction
    m = len(raw_comparisons)
    sorted_comps = sorted(raw_comparisons, key=lambda x: x["raw_p_value"])

    for rank, comp in enumerate(sorted_comps, start=1):
        adjusted_p = min(1.0, comp["raw_p_value"] * (m / rank))
        comp["adjusted_p_value"] = round(adjusted_p, 6)
        comp["significant"] = bool(adjusted_p < q_threshold)

    # Restore monotonicity in adjusted p-values (step-up)
    for k in range(m - 2, -1, -1):
        if sorted_comps[k]["adjusted_p_value"] > sorted_comps[k + 1]["adjusted_p_value"]:
            sorted_comps[k]["adjusted_p_value"] = sorted_comps[k + 1]["adjusted_p_value"]
            sorted_comps[k]["significant"] = bool(sorted_comps[k]["adjusted_p_value"] < q_threshold)

    return sorted_comps


def compute_directional_asymmetry_test(
    pos_degradations: List[float],
    neg_degradations: List[float],
) -> Dict[str, Any]:
    """Test directional asymmetry hypothesis (H2): Delta(+0.30) vs Delta(-0.30).

    Args:
        pos_degradations: Terminal degradations under positive petal shift (+0.30).
        neg_degradations: Terminal degradations under negative petal shift (-0.30).

    Returns:
        Dictionary with mean difference, paired t-test results, and null rejection flag.
    """
    v_pos = np.asarray(pos_degradations, dtype=np.float64)
    v_neg = np.asarray(neg_degradations, dtype=np.float64)

    if len(v_pos) != len(v_neg):
        raise ValueError("pos_degradations and neg_degradations must have identical length")

    diff = v_pos - v_neg
    mean_diff = float(np.mean(diff))

    if np.allclose(diff, 0.0):
        t_stat, p_val = 0.0, 1.0
    else:
        res = stats.ttest_rel(v_pos, v_neg)
        t_stat, p_val = float(res.statistic), float(res.pvalue)

    return {
        "test": "Paired Directional Asymmetry Test (H2)",
        "mean_positive_drop": round(float(np.mean(v_pos)), 4),
        "mean_negative_drop": round(float(np.mean(v_neg)), 4),
        "mean_difference": round(mean_diff, 4),
        "t_statistic": round(t_stat, 4),
        "p_value": round(p_val, 6),
        "null_rejected": bool(p_val < 0.05),
    }


def compute_dispersion_vs_translation_test(
    translation_audcs: List[float],
    dispersion_audcs: List[float],
) -> Dict[str, Any]:
    """Test dispersion vs translation degradation hypothesis (H4): AUDC_trans vs AUDC_disp.

    Args:
        translation_audcs: AUDC values under directional translation.
        dispersion_audcs: AUDC values under dispersion dilation.

    Returns:
        Dictionary with mean difference, paired t-test results, and null rejection flag.
    """
    v_trans = np.asarray(translation_audcs, dtype=np.float64)
    v_disp = np.asarray(dispersion_audcs, dtype=np.float64)

    if len(v_trans) != len(v_disp):
        raise ValueError("translation_audcs and dispersion_audcs must have identical length")

    diff = v_trans - v_disp
    mean_diff = float(np.mean(diff))

    if np.allclose(diff, 0.0):
        t_stat, p_val = 0.0, 1.0
    else:
        res = stats.ttest_rel(v_trans, v_disp)
        t_stat, p_val = float(res.statistic), float(res.pvalue)

    return {
        "test": "Translation vs Dispersion AUDC Test (H4)",
        "mean_translation_audc": round(float(np.mean(v_trans)), 4),
        "mean_dispersion_audc": round(float(np.mean(v_disp)), 4),
        "mean_difference": round(mean_diff, 4),
        "t_statistic": round(t_stat, 4),
        "p_value": round(p_val, 6),
        "null_rejected": bool(p_val < 0.05),
    }
