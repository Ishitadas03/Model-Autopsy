"""Multi-seed statistical evaluation, dispersion estimation, and Student's t confidence intervals."""

from dataclasses import asdict, dataclass
import math
from typing import Any, Dict, List, Optional
import numpy as np
from scipy import stats

from model_autopsy.analysis.failure_boundary import MANDATED_BOUNDARY_CAPTION


@dataclass
class SampleStatistics:
    """Statistical summary of sample metrics across independent experimental runs."""

    n: int
    mean: float
    sample_std: float  # Unbiased sample standard deviation (ddof=1)
    sem: float  # Standard error of the mean: sample_std / sqrt(n)
    df: int  # Degrees of freedom: n - 1
    t_critical: float  # Two-sided Student's t critical value
    margin_of_error: float  # t_critical * sem
    ci_lower: float  # mean - margin_of_error
    ci_upper: float  # mean + margin_of_error

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to serializable dictionary."""
        return asdict(self)


@dataclass
class SeverityAggregateStatistics:
    """Statistical metrics aggregated across all runs for a single severity level."""

    severity: float
    n_successful_runs: int
    n_failed_runs: int
    macro_f1: SampleStatistics
    accuracy: SampleStatistics
    absolute_degradation_pp: SampleStatistics
    relative_degradation_pct: SampleStatistics
    failure_count: int
    failure_proportion: float
    is_mean_failed: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregate statistics to serializable dictionary."""
        return {
            "severity": self.severity,
            "n_successful_runs": self.n_successful_runs,
            "n_failed_runs": self.n_failed_runs,
            "macro_f1": self.macro_f1.to_dict(),
            "accuracy": self.accuracy.to_dict(),
            "absolute_degradation_pp": self.absolute_degradation_pp.to_dict(),
            "relative_degradation_pct": self.relative_degradation_pct.to_dict(),
            "failure_count": self.failure_count,
            "failure_proportion": self.failure_proportion,
            "is_mean_failed": self.is_mean_failed,
        }


@dataclass
class MultiSeedEvaluationResult:
    """Comprehensive result of multi-seed research evaluation."""

    experiment_id: str
    seeds: List[int]
    severities: List[float]
    failure_threshold: float
    n_total_seeds: int
    n_successful_seeds: int
    n_failed_seeds: int
    failed_seed_details: List[Dict[str, Any]]
    per_seed_results: Dict[int, Dict[str, Any]]
    per_seed_boundaries: Dict[int, Optional[float]]
    severity_aggregates: List[SeverityAggregateStatistics]
    mean_observed_boundary: Optional[float]
    earliest_individual_boundary: Optional[float]
    boundary_caption: str
    monotonicity_summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert full multi-seed evaluation to serializable dictionary."""
        return {
            "experiment_id": self.experiment_id,
            "seeds": self.seeds,
            "severities": self.severities,
            "failure_threshold": self.failure_threshold,
            "n_total_seeds": self.n_total_seeds,
            "n_successful_seeds": self.n_successful_seeds,
            "n_failed_seeds": self.n_failed_seeds,
            "failed_seed_details": self.failed_seed_details,
            "per_seed_results": {str(k): v for k, v in self.per_seed_results.items()},
            "per_seed_boundaries": {str(k): v for k, v in self.per_seed_boundaries.items()},
            "severity_aggregates": [agg.to_dict() for agg in self.severity_aggregates],
            "mean_observed_boundary": self.mean_observed_boundary,
            "earliest_individual_boundary": self.earliest_individual_boundary,
            "boundary_caption": self.boundary_caption,
            "monotonicity_summary": self.monotonicity_summary,
        }


def compute_sample_statistics(
    values: List[float],
    confidence: float = 0.95,
) -> SampleStatistics:
    """Compute sample mean, sample standard deviation (ddof=1), SEM, and two-sided

    Student's t confidence interval.

    Formulations (Section 16 of protocol):
        mean = (1 / n) * sum(v_i)
        sample_std = sqrt((1 / (n - 1)) * sum((v_i - mean)^2))  [ddof=1]
        SEM = sample_std / sqrt(n)
        CI = [mean - t_crit * SEM, mean + t_crit * SEM]
        where t_crit = t_{alpha/2, n-1}

    Args:
        values: List of empirical observations across runs.
        confidence: Confidence level (default 0.95 for 95% CI).

    Returns:
        SampleStatistics dataclass instance.

    Raises:
        ValueError: If values list is empty.
    """
    if not values:
        raise ValueError("Cannot calculate sample statistics on empty values list.")

    n = len(values)
    val_arr = np.array(values, dtype=np.float64)
    mean_val = float(np.mean(val_arr))

    if n < 2:
        return SampleStatistics(
            n=n,
            mean=round(mean_val, 4),
            sample_std=0.0,
            sem=0.0,
            df=0,
            t_critical=0.0,
            margin_of_error=0.0,
            ci_lower=round(mean_val, 4),
            ci_upper=round(mean_val, 4),
        )

    # Sample standard deviation strictly with ddof=1
    sample_std = float(np.std(val_arr, ddof=1))
    sem = sample_std / math.sqrt(n)

    # Two-sided Student's t critical value with df = n - 1
    df = n - 1
    alpha = 1.0 - confidence
    t_critical = float(stats.t.ppf(1.0 - alpha / 2.0, df=df))

    margin_of_error = t_critical * sem
    ci_lower = mean_val - margin_of_error
    ci_upper = mean_val + margin_of_error

    return SampleStatistics(
        n=n,
        mean=round(mean_val, 4),
        sample_std=round(sample_std, 4),
        sem=round(sem, 4),
        df=df,
        t_critical=round(t_critical, 4),
        margin_of_error=round(margin_of_error, 4),
        ci_lower=round(ci_lower, 4),
        ci_upper=round(ci_upper, 4),
    )


def aggregate_multi_seed_results(
    per_seed_runs: Dict[int, Dict[str, Any]],
    severities: List[float],
    failure_threshold: float = 0.80,
    experiment_id: str = "E001",
    failed_seeds: Optional[List[Dict[str, Any]]] = None,
) -> MultiSeedEvaluationResult:
    """Aggregate individual seed evaluation trajectories into protocol-compliant statistical summaries.

    Args:
        per_seed_runs: Dictionary mapping seed to successful experiment execution result dictionary.
        severities: Ordered list of discrete severity levels.
        failure_threshold: Predefined primary failure threshold (default 0.80).
        experiment_id: Experiment ID string (default 'E001').
        failed_seeds: List of failure details for any aborted seed runs.

    Returns:
        MultiSeedEvaluationResult containing complete multi-seed statistical analysis.
    """
    failed_seeds = failed_seeds or []
    successful_seeds = sorted(list(per_seed_runs.keys()))
    n_successful = len(successful_seeds)
    n_failed = len(failed_seeds)
    total_seeds = n_successful + n_failed

    if n_successful == 0:
        raise ValueError("Cannot aggregate multi-seed results: zero successful runs.")

    # 1. Per-seed failure boundary extraction
    per_seed_boundaries: Dict[int, Optional[float]] = {}
    for seed, res in per_seed_runs.items():
        fb = res.get("failure_boundary", {})
        per_seed_boundaries[seed] = fb.get("observed_boundary")

    # 2. Severity-wise aggregation
    severity_aggregates: List[SeverityAggregateStatistics] = []
    for sev in severities:
        sev_float = float(sev)

        macro_f1_vals: List[float] = []
        acc_vals: List[float] = []
        abs_deg_vals: List[float] = []
        rel_deg_vals: List[float] = []
        fail_count = 0

        for seed in successful_seeds:
            rec_list = per_seed_runs[seed].get("severity_records", [])
            match = next((r for r in rec_list if abs(float(r["severity"]) - sev_float) < 1e-6), None)
            if match is not None:
                f1 = float(match["macro_f1"])
                macro_f1_vals.append(f1)
                acc_vals.append(float(match["accuracy"]))
                abs_deg_vals.append(float(match["absolute_degradation_pp"]))
                rel_deg_vals.append(float(match["relative_degradation_pct"]))
                if f1 < failure_threshold:
                    fail_count += 1

        stat_f1 = compute_sample_statistics(macro_f1_vals)
        stat_acc = compute_sample_statistics(acc_vals)
        stat_abs = compute_sample_statistics(abs_deg_vals)
        stat_rel = compute_sample_statistics(rel_deg_vals)

        fail_prop = round(fail_count / len(macro_f1_vals), 4) if macro_f1_vals else 0.0
        is_mean_failed = bool(stat_f1.mean < failure_threshold)

        severity_aggregates.append(
            SeverityAggregateStatistics(
                severity=sev_float,
                n_successful_runs=len(macro_f1_vals),
                n_failed_runs=n_failed,
                macro_f1=stat_f1,
                accuracy=stat_acc,
                absolute_degradation_pp=stat_abs,
                relative_degradation_pct=stat_rel,
                failure_count=fail_count,
                failure_proportion=fail_prop,
                is_mean_failed=is_mean_failed,
            )
        )

    # 3. Aggregate failure boundaries: Mean performance boundary vs Earliest individual boundary
    mean_boundary: Optional[float] = None
    for agg in severity_aggregates:
        if agg.is_mean_failed:
            mean_boundary = agg.severity
            break

    observed_individual_boundaries = [b for b in per_seed_boundaries.values() if b is not None]
    earliest_individual: Optional[float] = (
        min(observed_individual_boundaries) if observed_individual_boundaries else None
    )

    # 4. Monotonicity Analysis (Section 16.3 of protocol)
    # Check whether M_bar(s_k) >= M_bar(s_{k+1}) across consecutive steps
    monotonicity_steps = []
    is_strictly_monotonic = True
    for k in range(len(severity_aggregates) - 1):
        curr_sev = severity_aggregates[k].severity
        next_sev = severity_aggregates[k + 1].severity
        curr_mean = severity_aggregates[k].macro_f1.mean
        next_mean = severity_aggregates[k + 1].macro_f1.mean
        step_diff = round(curr_mean - next_mean, 4)
        is_step_decay = bool(curr_mean >= next_mean)
        if not is_step_decay:
            is_strictly_monotonic = False
        monotonicity_steps.append({
            "from_severity": curr_sev,
            "to_severity": next_sev,
            "from_mean_f1": curr_mean,
            "to_mean_f1": next_mean,
            "diff_pp": round(step_diff * 100.0, 2),
            "is_decay_or_equal": is_step_decay,
        })

    monotonicity_summary = {
        "is_strictly_monotonic": is_strictly_monotonic,
        "steps": monotonicity_steps,
        "note": (
            "Monotonic decay holds if each step exhibits non-increasing mean performance. "
            "Minor non-monotonic increases at low severity can occur when isotropic noise "
            "incidentally shifts ambiguous borderline points toward true class clusters."
        ),
    }

    return MultiSeedEvaluationResult(
        experiment_id=experiment_id,
        seeds=successful_seeds,
        severities=severities,
        failure_threshold=failure_threshold,
        n_total_seeds=total_seeds,
        n_successful_seeds=n_successful,
        n_failed_seeds=n_failed,
        failed_seed_details=failed_seeds,
        per_seed_results=per_seed_runs,
        per_seed_boundaries=per_seed_boundaries,
        severity_aggregates=severity_aggregates,
        mean_observed_boundary=mean_boundary,
        earliest_individual_boundary=earliest_individual,
        boundary_caption=MANDATED_BOUNDARY_CAPTION,
        monotonicity_summary=monotonicity_summary,
    )
