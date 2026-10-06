import { describe, it, expect } from 'vitest';
import { HERO_EXPERIMENT, MOCK_FAILED_SAMPLES } from '@/lib/mocks/experiments';
import { calculateDegradation, MANDATED_BOUNDARY_CAPTION, FEATURE_VULNERABILITY_CAVEAT } from '@/lib/metrics';

describe('EXP-0241 Hero Experiment Internal Consistency', () => {
  it('matches all specified hero experiment numbers exactly', () => {
    expect(HERO_EXPERIMENT.id).toBe('EXP-0241');
    expect(HERO_EXPERIMENT.modelName).toBe('Random Forest');
    expect(HERO_EXPERIMENT.datasetName).toBe('Credit Risk Demo (synthetic)');
    expect(HERO_EXPERIMENT.stressConfig.type).toBe('gaussian_noise');

    const results = HERO_EXPERIMENT.results!;
    expect(results.baselineMetrics.f1).toBe(0.958);
    expect(results.worstCaseMetrics.f1).toBe(0.712);
    expect(results.failureThreshold).toBe(0.8);
    expect(results.observedBoundary).toBe(0.231);
    expect(results.observedBoundaryLabel).toBe(MANDATED_BOUNDARY_CAPTION);

    // Degradation calculation check
    const degradation = calculateDegradation(
      'f1',
      results.baselineMetrics.f1,
      results.worstCaseMetrics.f1
    );
    expect(degradation.absolutePpText).toBe('-24.6 pp');
    expect(degradation.relativePercentText).toBe('-25.7%');

    // Statistical validation with 5 seeds
    expect(HERO_EXPERIMENT.numSeeds).toBe(5);
    expect(results.statisticalValidation).toBeDefined();
    expect(results.statisticalValidation?.ci95).toBe(0.024); // ± 2.4%

    // Most vulnerable feature
    expect(results.mostVulnerableFeature?.name).toBe('Credit Score');
    expect(results.mostVulnerableFeature?.caveat).toBe(FEATURE_VULNERABILITY_CAVEAT);

    // 143 failed samples count
    expect(results.failedSamplesCount).toBe(143);
    expect(MOCK_FAILED_SAMPLES.length).toBe(143);

    // Verify sample features
    const firstSample = MOCK_FAILED_SAMPLES[0];
    expect(firstSample.features).toHaveProperty('Credit Score');
    expect(firstSample.features).toHaveProperty('Income');
    expect(firstSample.features).toHaveProperty('Age');
    expect(firstSample.features).toHaveProperty('Loan Amount');
    expect(['Fraud', 'Normal']).toContain(firstSample.trueLabel);
  });
});
