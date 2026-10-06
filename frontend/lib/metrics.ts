/**
 * Direction-aware metric calculation & formatting utilities for Model Autopsy.
 * Enforces honesty rules across the application.
 */

export const MANDATED_BOUNDARY_CAPTION =
  'Observed failure boundary under the specified experimental configuration.';

export const FEATURE_VULNERABILITY_CAVEAT =
  'Empirical sensitivity — not a causal explanation.';

export type MetricType =
  | 'accuracy'
  | 'f1'
  | 'precision'
  | 'recall'
  | 'roc_auc'
  | 'pr_auc'
  | 'r2'
  | 'mae'
  | 'rmse'
  | 'loss';

export interface MetricDirectionInfo {
  higherIsBetter: boolean;
  isBoundedPercentage: boolean; // e.g. accuracy, f1 (0-1), vs unbounded regression
  unit?: string;
}

export const METRIC_DEFINITIONS: Record<MetricType, MetricDirectionInfo> = {
  accuracy: { higherIsBetter: true, isBoundedPercentage: true },
  f1: { higherIsBetter: true, isBoundedPercentage: true },
  precision: { higherIsBetter: true, isBoundedPercentage: true },
  recall: { higherIsBetter: true, isBoundedPercentage: true },
  roc_auc: { higherIsBetter: true, isBoundedPercentage: true },
  pr_auc: { higherIsBetter: true, isBoundedPercentage: true },
  r2: { higherIsBetter: true, isBoundedPercentage: false },
  mae: { higherIsBetter: false, isBoundedPercentage: false },
  rmse: { higherIsBetter: false, isBoundedPercentage: false },
  loss: { higherIsBetter: false, isBoundedPercentage: false },
};

export interface MetricDegradationResult {
  baseline: number;
  current: number;
  absoluteDiff: number; // current - baseline
  relativeDiffPercent: number; // percentage change relative to baseline
  isDegraded: boolean; // true if performance got worse
  isImproved: boolean; // true if performance got better
  absolutePpText?: string; // e.g. "-24.6 pp" for bounded metrics
  relativePercentText: string; // e.g. "-25.7%"
  displayText: string; // e.g. "-24.6 pp (-25.7%)"
}

/**
 * Calculates honest degradation between baseline and current metrics.
 * Baseline and current are assumed to be in normal scale (e.g. 0.958 for 95.8% F1, or raw MAE).
 */
export function calculateDegradation(
  metric: MetricType,
  baseline: number,
  current: number
): MetricDegradationResult {
  const def = METRIC_DEFINITIONS[metric] || { higherIsBetter: true, isBoundedPercentage: false };
  const diff = current - baseline;

  // Relative diff is based on baseline magnitude
  const relativePercent = baseline !== 0 ? (diff / Math.abs(baseline)) * 100 : 0;

  // Determine degradation vs improvement
  const isDegraded = def.higherIsBetter ? diff < -1e-6 : diff > 1e-6;
  const isImproved = def.higherIsBetter ? diff > 1e-6 : diff < -1e-6;

  let absolutePpText: string | undefined = undefined;
  if (def.isBoundedPercentage) {
    // For 0-1 metrics, 0.958 - 0.712 = 0.246 -> 24.6 percentage points (pp)
    const pp = diff * 100;
    const sign = pp > 0 ? '+' : '';
    absolutePpText = `${sign}${pp.toFixed(1)} pp`;
  }

  const relSign = relativePercent > 0 ? '+' : '';
  const relativePercentText = `${relSign}${relativePercent.toFixed(1)}%`;

  const displayText = absolutePpText
    ? `${absolutePpText} (${relativePercentText})`
    : `${diff > 0 ? '+' : ''}${diff.toFixed(2)} (${relativePercentText})`;

  return {
    baseline,
    current,
    absoluteDiff: diff,
    relativeDiffPercent: relativePercent,
    isDegraded,
    isImproved,
    absolutePpText,
    relativePercentText,
    displayText,
  };
}

/**
 * Formats a metric value or an honest reason if skipped.
 */
export function formatMetricValue(
  value: number | null | undefined,
  metric: MetricType,
  skippedReason?: string
): string {
  if (value === null || value === undefined) {
    return skippedReason ? `Not computed — ${skippedReason}` : 'Not computed — unavailable';
  }
  const def = METRIC_DEFINITIONS[metric];
  if (def?.isBoundedPercentage) {
    return `${(value * 100).toFixed(1)}%`;
  }
  return value.toFixed(3);
}
