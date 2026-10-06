import { describe, it, expect } from 'vitest';
import {
  ExperimentSchema,
  StressConfigSchema,
  DatasetSchema,
  ModelAdapterSchema,
} from '@/lib/schemas';

describe('Zod Domain Schemas', () => {
  it('validates a valid stress configuration', () => {
    const validConfig = {
      type: 'gaussian_noise',
      severityLevels: [0.05, 0.1, 0.2, 0.3],
      mode: 'random',
    };
    expect(() => StressConfigSchema.parse(validConfig)).not.toThrow();
  });

  it('rejects invalid stress types', () => {
    const invalidConfig = {
      type: 'unsupported_magic_stress',
      severityLevels: [0.1],
    };
    expect(() => StressConfigSchema.parse(invalidConfig)).toThrow();
  });

  it('validates a dataset schema', () => {
    const dataset = {
      id: 'credit-risk-demo',
      name: 'Credit Risk Demo',
      description: 'Synthetic benchmark dataset',
      sampleCount: 1000,
      featureCount: 4,
      classCount: 2,
      taskType: 'classification',
      features: [
        { name: 'Income', type: 'numeric', missingCount: 0 },
        { name: 'Credit Score', type: 'numeric', missingCount: 0 },
      ],
    };
    const parsed = DatasetSchema.parse(dataset);
    expect(parsed.id).toBe('credit-risk-demo');
    expect(parsed.isCustom).toBe(false); // default
  });

  it('validates model adapters strictly requiring scikit-learn framework', () => {
    const model = {
      id: 'random-forest',
      name: 'Random Forest',
      framework: 'scikit-learn',
      taskTypes: ['classification'],
      predictProba: true,
      description: 'Tree ensemble',
      parameters: { n_estimators: 100 },
    };
    expect(() => ModelAdapterSchema.parse(model)).not.toThrow();

    const invalidModel = {
      ...model,
      framework: 'pytorch', // Prompt rule: only supported adapters (scikit-learn)
    };
    expect(() => ModelAdapterSchema.parse(invalidModel)).toThrow();
  });
});
