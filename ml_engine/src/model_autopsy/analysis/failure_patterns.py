"""Fine-grained sample-level failure pattern analysis for Model Autopsy (RQ7)."""

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import scipy.stats as stats


def calculate_exact_binomial_ci(
    k: int, n: int, confidence: float = 0.95
) -> Tuple[float, float]:
    """Compute exact two-sided Clopper-Pearson binomial confidence interval.

    Args:
        k: Number of observed events (e.g. misclassified instances).
        n: Total number of trials (e.g. sample size N_test=30 or n_k=10).
        confidence: Confidence level (default 0.95 for 95% CI).

    Returns:
        Tuple of (ci_lower, ci_upper) bounded in [0.0, 1.0].
    """
    if n <= 0:
        return 0.0, 0.0
    if k < 0 or k > n:
        raise ValueError(f"k must be in range [0, n], received k={k}, n={n}")

    alpha = 1.0 - confidence
    lower = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2.0, k, n - k + 1))
    upper = 1.0 if k == n else float(stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
    return round(float(lower), 4), round(float(upper), 4)


def apply_benjamini_hochberg(
    p_values: List[float], q: float = 0.05
) -> List[Dict[str, Any]]:
    """Apply the Benjamini-Hochberg procedure for False Discovery Rate (FDR) control.

    Args:
        p_values: List of raw p-values from multiple statistical tests.
        q: Target FDR threshold (default 0.05).

    Returns:
        List of dictionaries with rank, raw p-value, adjusted critical threshold,
        adjusted p-value (q-value), and significance boolean.
    """
    m = len(p_values)
    if m == 0:
        return []

    # Pair with original indices
    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    results = [None] * m

    # Step-up threshold: p_(i) <= (i / m) * q
    max_significant_rank = -1
    for rank_1idx, (orig_idx, p_val) in enumerate(indexed_p, start=1):
        crit = (rank_1idx / float(m)) * q
        if p_val <= crit:
            max_significant_rank = rank_1idx

    # Compute step-down adjusted p-values
    adjusted = [0.0] * m
    cum_min = 1.0
    for rank_1idx in range(m, 0, -1):
        orig_idx, p_val = indexed_p[rank_1idx - 1]
        adj = (float(m) / float(rank_1idx)) * p_val
        cum_min = min(cum_min, adj)
        adjusted[rank_1idx - 1] = min(1.0, cum_min)

    for rank_1idx, (orig_idx, p_val) in enumerate(indexed_p, start=1):
        crit = (rank_1idx / float(m)) * q
        is_sig = rank_1idx <= max_significant_rank
        results[orig_idx] = {
            "rank": rank_1idx,
            "raw_p": round(float(p_val), 6),
            "bh_critical_threshold": round(float(crit), 6),
            "adjusted_p": round(float(adjusted[rank_1idx - 1]), 6),
            "is_significant_fdr": bool(is_sig),
        }

    return results


def calculate_sample_errors(
    y_true: np.ndarray, y_pred: np.ndarray
) -> np.ndarray:
    """Compute binary misclassification indicator vector e_i = I(y_pred_i != y_true_i).

    Args:
        y_true: 1D array of ground truth class labels of length N.
        y_pred: 1D array of predicted class labels of length N.

    Returns:
        1D boolean array of length N (True = misclassified).
    """
    if y_true.shape != y_pred.shape:
        raise ValueError(
            f"Shape mismatch: y_true shape {y_true.shape} != y_pred shape {y_pred.shape}"
        )
    return y_pred != y_true


def calculate_error_persistence(
    predictions_by_severity: Dict[float, np.ndarray],
    y_true: np.ndarray,
    severities: List[float],
) -> Dict[str, Any]:
    """Calculate sample-level first-error severity, error persistence ratio, and oscillation count.

    Boundary cases:
        - Never-failing sample: s*(i) is None (unobserved, > max severity).
          EPR is None/NA (excluded from mean EPR). POC is 0.
        - First failure at maximum severity (e.g. s = 0.30):
          Denominator |{s >= s*}| = 1. EPR = 1.0.
        - Prediction oscillation count (POC):
          Counts adjacent transitions across the ordered severity grid.

    Args:
        predictions_by_severity: Dict mapping severity float to 1D array of predictions.
        y_true: 1D array of ground truth labels of length N.
        severities: Sorted list of severity levels [s_0, s_1, ..., s_{k-1}].

    Returns:
        Dict mapping sample index to persistence record, plus overall summary statistics.
    """
    sorted_sevs = sorted(severities)
    n_samples = len(y_true)

    sample_records: List[Dict[str, Any]] = []

    for i in range(n_samples):
        true_label = int(y_true[i])
        pred_sequence = [int(predictions_by_severity[s][i]) for s in sorted_sevs]
        error_sequence = [pred != true_label for pred in pred_sequence]

        # 1. First-error severity
        first_err_idx = None
        for idx, is_err in enumerate(error_sequence):
            if is_err:
                first_err_idx = idx
                break

        if first_err_idx is None:
            first_error_severity: Optional[float] = None
            epr: Optional[float] = None
        else:
            first_error_severity = sorted_sevs[first_err_idx]
            # S_tail = {s in S : s >= s*(i)}
            tail_errors = error_sequence[first_err_idx:]
            denominator = len(tail_errors)
            numerator = sum(tail_errors)
            epr = float(numerator) / float(denominator) if denominator > 0 else 1.0

        # 2. Prediction oscillation count (adjacent transitions)
        poc = 0
        for j in range(len(pred_sequence) - 1):
            if pred_sequence[j] != pred_sequence[j + 1]:
                poc += 1

        rec = {
            "sample_index": i,
            "true_label": true_label,
            "first_error_severity": first_error_severity,
            "is_ever_failed": first_err_idx is not None,
            "error_persistence_ratio": round(epr, 4) if epr is not None else None,
            "prediction_oscillation_count": poc,
            "predictions_by_severity": {
                str(s): pred_sequence[j] for j, s in enumerate(sorted_sevs)
            },
            "error_sequence": error_sequence,
        }
        sample_records.append(rec)

    # Compute aggregate summary across samples
    failed_samples = [r for r in sample_records if r["is_ever_failed"]]
    valid_eprs = [
        r["error_persistence_ratio"]
        for r in sample_records
        if r["error_persistence_ratio"] is not None
    ]

    mean_epr = float(np.mean(valid_eprs)) if valid_eprs else None
    perfect_persistence_count = sum(1 for e in valid_eprs if abs(e - 1.0) < 1e-6)
    oscillating_samples_count = sum(
        1 for r in sample_records if r["prediction_oscillation_count"] > 1
    )

    return {
        "sample_records": sample_records,
        "n_total_samples": n_samples,
        "n_failed_samples": len(failed_samples),
        "n_resilient_samples": n_samples - len(failed_samples),
        "mean_error_persistence_ratio": (
            round(mean_epr, 4) if mean_epr is not None else None
        ),
        "perfect_persistence_count": perfect_persistence_count,
        "perfect_persistence_proportion": (
            round(perfect_persistence_count / len(failed_samples), 4)
            if failed_samples
            else 1.0
        ),
        "oscillating_samples_count": oscillating_samples_count,
    }


def calculate_jaccard_similarity(
    error_set_a: Set[int], error_set_b: Set[int]
) -> float:
    """Compute Jaccard similarity index J(A, B) = |A ∩ B| / |A ∪ B|.

    Boundary condition: If both error sets are empty (zero errors for both models),
    Jaccard similarity is 1.0 (perfect concordance on resilience).

    Args:
        error_set_a: Set of sample indices failed by model A.
        error_set_b: Set of sample indices failed by model B.

    Returns:
        Jaccard similarity float in [0.0, 1.0].
    """
    if len(error_set_a) == 0 and len(error_set_b) == 0:
        return 1.0
    union_len = len(error_set_a.union(error_set_b))
    if union_len == 0:
        return 1.0
    intersection_len = len(error_set_a.intersection(error_set_b))
    return round(float(intersection_len) / float(union_len), 4)


def calculate_inter_model_concordance(
    predictions_by_model: Dict[str, np.ndarray], y_true: np.ndarray
) -> Dict[str, Any]:
    """Calculate error-set overlap, pairwise Jaccard similarities, and consensus failures.

    Args:
        predictions_by_model: Dict mapping model_name to 1D prediction array.
        y_true: 1D array of ground truth labels.

    Returns:
        Dict containing pairwise Jaccard similarities, consensus failure indices,
        and algorithm-unique error counts.
    """
    models = list(predictions_by_model.keys())
    error_sets: Dict[str, Set[int]] = {}

    for m in models:
        preds = predictions_by_model[m]
        err_indices = set(np.where(preds != y_true)[0].tolist())
        error_sets[m] = err_indices

    # Pairwise Jaccard matrix
    pairwise_jaccard: Dict[str, float] = {}
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            m1, m2 = models[i], models[j]
            j_score = calculate_jaccard_similarity(error_sets[m1], error_sets[m2])
            pairwise_jaccard[f"{m1}_vs_{m2}"] = j_score

    # Consensus errors: instances failed by ALL models
    all_sets = list(error_sets.values())
    consensus_set = set.intersection(*all_sets) if all_sets else set()

    # Model-unique errors: instances failed ONLY by model m
    unique_errors: Dict[str, List[int]] = {}
    for m in models:
        other_sets = [error_sets[o] for o in models if o != m]
        other_union = set.union(*other_sets) if other_sets else set()
        unique = error_sets[m].difference(other_union)
        unique_errors[m] = sorted(list(unique))

    return {
        "error_set_sizes": {m: len(error_sets[m]) for m in models},
        "error_indices": {m: sorted(list(error_sets[m])) for m in models},
        "pairwise_jaccard": pairwise_jaccard,
        "consensus_error_count": len(consensus_set),
        "consensus_error_indices": sorted(list(consensus_set)),
        "unique_error_counts": {m: len(unique_errors[m]) for m in models},
        "unique_error_indices": unique_errors,
    }


def calculate_class_vulnerabilities(
    y_pred: np.ndarray,
    y_true: np.ndarray,
    target_names: List[str],
) -> Dict[str, Any]:
    """Calculate class-wise error rates, Clopper-Pearson CIs, and directed confusion counts.

    Args:
        y_pred: 1D array of predicted labels.
        y_true: 1D array of true labels.
        target_names: List of class names (e.g. ['setosa', 'versicolor', 'virginica']).

    Returns:
        Dict containing class-wise error rates with exact binomial CIs and confusion counts.
    """
    n_classes = len(target_names)
    class_results: Dict[str, Any] = {}

    for k in range(n_classes):
        class_name = target_names[k]
        class_mask = y_true == k
        n_k = int(np.sum(class_mask))
        if n_k == 0:
            continue

        errors_k = int(np.sum((y_pred != y_true) & class_mask))
        error_rate = float(errors_k) / float(n_k)
        ci_low, ci_high = calculate_exact_binomial_ci(errors_k, n_k, confidence=0.95)

        class_results[class_name] = {
            "class_index": k,
            "n_samples": n_k,
            "error_count": errors_k,
            "error_rate": round(error_rate, 4),
            "ci_95": [ci_low, ci_high],
        }

    # Directed confusion between class 1 (versicolor) and class 2 (virginica)
    v_to_vg = int(np.sum((y_true == 1) & (y_pred == 2)))
    vg_to_v = int(np.sum((y_true == 2) & (y_pred == 1)))
    s_to_v = int(np.sum((y_true == 0) & (y_pred == 1)))
    s_to_vg = int(np.sum((y_true == 0) & (y_pred == 2)))

    return {
        "per_class": class_results,
        "directed_confusions": {
            "versicolor_to_virginica": v_to_vg,
            "virginica_to_versicolor": vg_to_v,
            "setosa_to_versicolor": s_to_v,
            "setosa_to_virginica": s_to_vg,
        },
    }


def calculate_mahalanobis_margins(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    early_failure_indices: Set[int],
    resilient_indices: Set[int],
    ridge_eps: float = 1e-6,
) -> Dict[str, Any]:
    """Compute clean-space training pooled covariance, test Mahalanobis margins,

    and non-parametric Mann-Whitney U test contrasting early-failing vs resilient samples.

    Strict leakage guarantee:
        Class centroids and pooled covariance matrix are fitted STRICTLY on X_train.
        X_test is evaluated strictly against frozen training parameters.

    Args:
        X_train: Training feature array (N_train, D).
        y_train: Training class label array (N_train,).
        X_test: Test feature array (N_test, D).
        y_test: Test class label array (N_test,).
        early_failure_indices: Set of test indices failing early (s* <= 0.15).
        resilient_indices: Set of test indices never failing (s* > 0.30).
        ridge_eps: Tikhonov regularization scalar added to diagonal.

    Returns:
        Dict containing per-sample margins, group statistics, and Mann-Whitney U test.
    """
    classes = np.unique(y_train)
    n_train, n_features = X_train.shape
    k_classes = len(classes)

    # 1. Training class centroids
    centroids: Dict[int, np.ndarray] = {}
    for c in classes:
        centroids[int(c)] = np.mean(X_train[y_train == c], axis=0)

    # 2. Pooled training covariance with degrees of freedom (N_train - K)
    pooled_cov = np.zeros((n_features, n_features), dtype=np.float64)
    for c in classes:
        X_c = X_train[y_train == c]
        diff = X_c - centroids[int(c)]
        pooled_cov += diff.T @ diff
    pooled_cov /= float(n_train - k_classes)

    # 3. Ridge regularization to ensure numerical conditioning
    cov_reg = pooled_cov + ridge_eps * np.eye(n_features)
    cov_inv = np.linalg.inv(cov_reg)

    # 4. Compute test Mahalanobis distances and margins
    sample_margins: List[Dict[str, Any]] = []
    early_margins: List[float] = []
    resilient_margins: List[float] = []

    for i in range(len(X_test)):
        x_i = X_test[i]
        true_c = int(y_test[i])

        # Distance to true class centroid
        diff_true = x_i - centroids[true_c]
        d_true = float(np.sqrt(np.dot(np.dot(diff_true, cov_inv), diff_true)))

        # Distance to nearest competing class centroid
        d_competing = float("inf")
        nearest_competing_class = None
        for other_c in classes:
            if other_c == true_c:
                continue
            diff_other = x_i - centroids[int(other_c)]
            d_other = float(np.sqrt(np.dot(np.dot(diff_other, cov_inv), diff_other)))
            if d_other < d_competing:
                d_competing = d_other
                nearest_competing_class = int(other_c)

        # Margin: competing distance - true distance
        margin = d_competing - d_true
        rec = {
            "sample_index": i,
            "true_class": true_c,
            "nearest_competing_class": nearest_competing_class,
            "distance_to_true_centroid": round(d_true, 4),
            "distance_to_competing_centroid": round(d_competing, 4),
            "opposing_class_margin": round(margin, 4),
        }
        sample_margins.append(rec)

        if i in early_failure_indices:
            early_margins.append(margin)
        if i in resilient_indices:
            resilient_margins.append(margin)

    # 5. Non-parametric hypothesis test: Mann-Whitney U test
    mwu_stat = None
    mwu_p = None
    effect_size_r = None

    if len(early_margins) > 0 and len(resilient_margins) > 0:
        # One-sided: early failing instances have significantly SMALLER clean margins
        res = stats.mannwhitneyu(early_margins, resilient_margins, alternative="less")
        mwu_stat = float(res.statistic)
        mwu_p = float(res.pvalue)

        # Rank-biserial correlation effect size r = 1 - (2U / (n1 * n2))
        n1, n2 = len(early_margins), len(resilient_margins)
        effect_size_r = round(float(1.0 - (2.0 * mwu_stat) / (n1 * n2)), 4)

    return {
        "sample_margins": sample_margins,
        "early_failing_group": {
            "n_samples": len(early_margins),
            "mean_margin": (
                round(float(np.mean(early_margins)), 4) if early_margins else None
            ),
            "std_margin": (
                round(float(np.std(early_margins, ddof=1)), 4)
                if len(early_margins) > 1
                else 0.0
            ),
        },
        "resilient_group": {
            "n_samples": len(resilient_margins),
            "mean_margin": (
                round(float(np.mean(resilient_margins)), 4)
                if resilient_margins
                else None
            ),
            "std_margin": (
                round(float(np.std(resilient_margins, ddof=1)), 4)
                if len(resilient_margins) > 1
                else 0.0
            ),
        },
        "hypothesis_test": {
            "test_name": "Mann-Whitney U Test (Alternative: early < resilient)",
            "u_statistic": mwu_stat,
            "p_value": round(mwu_p, 6) if mwu_p is not None else None,
            "rank_biserial_effect_size_r": effect_size_r,
            "is_significant_alpha_05": mwu_p < 0.05 if mwu_p is not None else False,
            "caveat": "Empirical sensitivity — not a causal explanation.",
        },
    }


def calculate_seed_stability(
    predictions_across_seeds: List[np.ndarray], y_true: np.ndarray
) -> Dict[str, Any]:
    """Calculate cross-seed failure stability frequency Phi(i) and classify samples.

    Categories:
        - Core Hard: Failed in >= 80% of seeds (>= 4 of 5 seeds).
        - Seed-Vulnerable: Failed in 1 to 3 seeds (20% to 60%).
        - Resilient: Failed in 0 seeds (0%).

    Args:
        predictions_across_seeds: List of 1D arrays of length N_test, one array per research seed.
        y_true: 1D array of ground truth labels.

    Returns:
        Dict containing per-sample stability records and summary categorization counts.
    """
    n_seeds = len(predictions_across_seeds)
    n_samples = len(y_true)

    sample_stabilities: List[Dict[str, Any]] = []
    category_counts = {"core_hard": 0, "seed_vulnerable": 0, "resilient": 0}

    for i in range(n_samples):
        true_label = int(y_true[i])
        error_count = sum(
            1 for seed_preds in predictions_across_seeds if seed_preds[i] != true_label
        )
        frequency = float(error_count) / float(n_seeds)

        if frequency >= 0.8:
            cat = "core_hard"
        elif frequency > 0.0:
            cat = "seed_vulnerable"
        else:
            cat = "resilient"

        category_counts[cat] += 1
        sample_stabilities.append(
            {
                "sample_index": i,
                "true_label": true_label,
                "seed_error_count": error_count,
                "n_seeds": n_seeds,
                "failure_frequency": round(frequency, 4),
                "category": cat,
            }
        )

    return {
        "sample_stabilities": sample_stabilities,
        "category_counts": category_counts,
        "category_proportions": {
            cat: round(count / float(n_samples), 4)
            for cat, count in category_counts.items()
        },
    }
