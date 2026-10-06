import { describe, it, expect } from 'vitest';
import { validateStep, Step4Schema } from '@/lib/validators';

describe('Workspace Stepper Validation Gates', () => {
  it('validates Step 1 Dataset requirements', () => {
    // Missing dataset
    const invalid = validateStep(1, {});
    expect(invalid.isValid).toBe(false);
    expect(invalid.error).toBeDefined();

    // Valid dataset
    const valid = validateStep(1, {
      datasetId: 'credit-risk-demo',
      datasetName: 'Credit Risk Demo',
      taskType: 'classification',
    });
    expect(valid.isValid).toBe(true);
  });

  it('validates Step 2 Model adapter requirements', () => {
    // Missing model
    const invalid = validateStep(2, {});
    expect(invalid.isValid).toBe(false);

    // Valid model
    const valid = validateStep(2, {
      modelId: 'random-forest-classifier',
      modelName: 'Random Forest',
    });
    expect(valid.isValid).toBe(true);
  });

  it('validates Step 3 Baseline split bounds', () => {
    // Out of bounds test size (> 0.50)
    const tooHigh = validateStep(3, { testSize: 0.65, seed: 42 });
    expect(tooHigh.isValid).toBe(false);

    // Out of bounds test size (< 0.05)
    const tooLow = validateStep(3, { testSize: 0.02, seed: 42 });
    expect(tooLow.isValid).toBe(false);

    // Valid split
    const valid = validateStep(3, { testSize: 0.2, seed: 42 });
    expect(valid.isValid).toBe(true);
  });

  it('validates Step 4 Stress Test severities and allowed types', () => {
    // Invalid stress type (outliers is coming soon / not enabled)
    const invalidType = validateStep(4, {
      stressType: 'outliers' as any,
      severityLevels: [0.1],
      stressMode: 'random',
      metric: 'f1',
      failureThreshold: 0.8,
    });
    expect(invalidType.isValid).toBe(false);

    // Severity level below 5%
    const belowMin = validateStep(4, {
      stressType: 'gaussian_noise',
      severityLevels: [0.02],
      stressMode: 'random',
      metric: 'f1',
      failureThreshold: 0.8,
    });
    expect(belowMin.isValid).toBe(false);

    // Severity level above 30%
    const aboveMax = validateStep(4, {
      stressType: 'gaussian_noise',
      severityLevels: [0.35],
      stressMode: 'random',
      metric: 'f1',
      failureThreshold: 0.8,
    });
    expect(aboveMax.isValid).toBe(false);

    // Feature-specific mode requires target features
    const missingTarget = validateStep(4, {
      stressType: 'gaussian_noise',
      severityLevels: [0.1, 0.2],
      stressMode: 'feature_specific',
      targetFeatures: [],
      metric: 'f1',
      failureThreshold: 0.8,
    });
    expect(missingTarget.isValid).toBe(false);

    // Valid Gaussian Noise stress test
    const valid = validateStep(4, {
      stressType: 'gaussian_noise',
      severityLevels: [0.05, 0.1, 0.2, 0.3],
      stressMode: 'random',
      metric: 'f1',
      failureThreshold: 0.8,
    });
    expect(valid.isValid).toBe(true);
  });
});
