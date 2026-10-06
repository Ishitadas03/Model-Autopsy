import { describe, it, expect } from 'vitest';
import {
  MANDATED_BOUNDARY_CAPTION,
  FEATURE_VULNERABILITY_CAVEAT,
  calculateDegradation,
} from '@/lib/metrics';
import { computeBoundary } from '@/components/results/BoundarySimulator';

describe('Results & Boundary Honesty Rules', () => {
  it('mandated boundary caption matches the required spec verbatim', () => {
    expect(MANDATED_BOUNDARY_CAPTION).toBe(
      'Observed failure boundary under the specified experimental configuration.'
    );
  });

  it('feature vulnerability caveat matches the required spec verbatim', () => {
    expect(FEATURE_VULNERABILITY_CAVEAT).toBe(
      'Empirical sensitivity — not a causal explanation.'
    );
  });

  it('direction-aware degradation works correctly for higher-is-better metrics (F1)', () => {
    // 95.8% baseline dropping to 71.2%
    const res = calculateDegradation('f1', 0.958, 0.712);

    expect(res.isDegraded).toBe(true);
    expect(res.isImproved).toBe(false);
    expect(res.absolutePpText).toBe('-24.6 pp');
    expect(res.relativePercentText).toBe('-25.7%');
  });

  it('direction-aware degradation works correctly for lower-is-better metrics (MAE)', () => {
    // Baseline MAE 18420 increasing to 24500 (worse)
    const res = calculateDegradation('mae', 18420, 24500);

    expect(res.isDegraded).toBe(true);
    expect(res.isImproved).toBe(false);
    expect(res.relativeDiffPercent).toBeGreaterThan(0);

    // If MAE drops from 18420 to 15000 (better)
    const improved = calculateDegradation('mae', 18420, 15000);
    expect(improved.isDegraded).toBe(false);
    expect(improved.isImproved).toBe(true);
  });

  it('computes failure boundary via linear interpolation accurately', () => {
    const testCurve = [
      { severity: 0, score: 0.958 },
      { severity: 0.1, score: 0.9 },
      { severity: 0.2, score: 0.824 },
      { severity: 0.3, score: 0.712 },
    ];

    // Failure threshold = 0.80
    // Between severity 0.2 (0.824) and severity 0.3 (0.712)
    // Diff: 0.824 - 0.712 = 0.112
    // Fraction: (0.824 - 0.80) / 0.112 = 0.024 / 0.112 ≈ 0.214
    // Boundary: 0.2 + 0.214 * 0.1 ≈ 0.221
    const boundary = computeBoundary(0.8, testCurve, false);
    expect(boundary).toBeGreaterThan(0.2);
    expect(boundary).toBeLessThan(0.3);

    // If threshold is not crossed within range (e.g. 0.60)
    const unreached = computeBoundary(0.6, testCurve, false);
    expect(unreached).toBeNull();
  });
});
