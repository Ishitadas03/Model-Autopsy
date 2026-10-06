import { describe, it, expect } from 'vitest';
import {
  calculateDegradation,
  formatMetricValue,
  MANDATED_BOUNDARY_CAPTION,
  FEATURE_VULNERABILITY_CAVEAT,
} from '@/lib/metrics';

describe('Honesty and Direction-Aware Metrics', () => {
  it('mandated boundary caption matches exact specified copy', () => {
    expect(MANDATED_BOUNDARY_CAPTION).toBe(
      'Observed failure boundary under the specified experimental configuration.'
    );
  });

  it('feature vulnerability caveat matches exact specified copy', () => {
    expect(FEATURE_VULNERABILITY_CAVEAT).toBe(
      'Empirical sensitivity — not a causal explanation.'
    );
  });

  describe('calculateDegradation', () => {
    it('calculates F1 score degradation with percentage points and relative percentage', () => {
      // 95.8% baseline to 71.2% worst case
      const res = calculateDegradation('f1', 0.958, 0.712);

      expect(res.isDegraded).toBe(true);
      expect(res.isImproved).toBe(false);
      // Absolute change in percentage points
      expect(res.absolutePpText).toBe('-24.6 pp');
      // Relative change in percentage
      expect(res.relativePercentText).toBe('-25.7%');
      expect(res.displayText).toBe('-24.6 pp (-25.7%)');
    });

    it('correctly handles lower-is-better metrics (MAE regression)', () => {
      // For MAE, an increase from 10 to 15 is degradation (worse performance)
      const res = calculateDegradation('mae', 10.0, 15.0);

      expect(res.isDegraded).toBe(true);
      expect(res.isImproved).toBe(false);
      expect(res.relativePercentText).toBe('+50.0%');
      expect(res.displayText).toBe('+5.00 (+50.0%)');
    });

    it('correctly handles lower-is-better metric improvements (MAE decrease)', () => {
      // For MAE, a decrease from 15 to 10 is improvement
      const res = calculateDegradation('mae', 15.0, 10.0);

      expect(res.isDegraded).toBe(false);
      expect(res.isImproved).toBe(true);
      expect(res.relativePercentText).toBe('-33.3%');
    });

    it('correctly handles higher-is-better metric improvements (Accuracy increase)', () => {
      const res = calculateDegradation('accuracy', 0.80, 0.85);

      expect(res.isDegraded).toBe(false);
      expect(res.isImproved).toBe(true);
      expect(res.absolutePpText).toBe('+5.0 pp');
      expect(res.relativePercentText).toBe('+6.2%');
    });
  });

  describe('formatMetricValue', () => {
    it('formats bounded percentage metrics with one decimal', () => {
      expect(formatMetricValue(0.958, 'f1')).toBe('95.8%');
    });

    it('formats unbounded regression metrics with three decimals', () => {
      expect(formatMetricValue(12.3456, 'mae')).toBe('12.346');
    });

    it('returns honest reason when metric is skipped / not computed', () => {
      expect(formatMetricValue(null, 'roc_auc', 'Single class in fold')).toBe(
        'Not computed — Single class in fold'
      );
      expect(formatMetricValue(undefined, 'f1')).toBe(
        'Not computed — unavailable'
      );
    });
  });
});
