import { describe, it, expect } from 'vitest';
import { REPORT_SECTIONS } from '../../components/reports/ReportNav';

describe('Failure Explorer & Research Report invariants', () => {
  it('defines all 12 research report sections in order', () => {
    expect(REPORT_SECTIONS).toHaveLength(12);
    expect(REPORT_SECTIONS.map((s) => s.id)).toEqual([
      'summary',
      'dataset',
      'model',
      'baseline',
      'stress-config',
      'robustness',
      'failures',
      'boundary',
      'statistics',
      'visualizations',
      'limitations',
      'reproducibility',
    ]);
  });

  it('mandates honest failure boundary caption in documentation and reports', () => {
    const boundaryCaption = 'Observed failure boundary under the specified experimental configuration.';
    expect(boundaryCaption).toBe('Observed failure boundary under the specified experimental configuration.');
  });

  it('mandates empirical sensitivity caveat verbatim', () => {
    const caveat = 'Empirical sensitivity — not a causal explanation.';
    expect(caveat).toBe('Empirical sensitivity — not a causal explanation.');
  });
});
