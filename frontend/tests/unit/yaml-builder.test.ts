import { describe, it, expect } from 'vitest';
import {
  generateExperimentYaml,
  generateManifestJson,
  WorkspaceConfig,
} from '@/lib/yaml';

describe('YAML & Manifest Serialization', () => {
  const sampleConfig: WorkspaceConfig = {
    datasetId: 'credit-risk-demo',
    datasetName: 'Credit Risk Demo (synthetic)',
    taskType: 'classification',
    modelId: 'random-forest-classifier',
    modelName: 'Random Forest Classifier',
    modelParams: {
      n_estimators: 100,
      max_depth: 10,
    },
    testSize: 0.2,
    seed: 42,
    numSeeds: 5,
    stressType: 'gaussian_noise',
    severityLevels: [0.05, 0.1, 0.2, 0.3],
    stressMode: 'random',
    metric: 'f1',
    failureThreshold: 0.8,
  };

  it('generates valid YAML containing required spec sections', () => {
    const yaml = generateExperimentYaml(sampleConfig);

    expect(yaml).toContain('version: "1.0"');
    expect(yaml).toContain('task_type: classification');
    expect(yaml).toContain('id: "credit-risk-demo"');
    expect(yaml).toContain('adapter: "random-forest-classifier"');
    expect(yaml).toContain('framework: "scikit-learn"');
    expect(yaml).toContain('n_estimators: 100');
    expect(yaml).toContain('type: gaussian_noise');
    expect(yaml).toContain('severity_levels: [0.05, 0.10, 0.20, 0.30]');
    expect(yaml).toContain('failure_threshold: 0.8');
    expect(yaml).toContain('stratify: true');
  });

  it('generates parseable Manifest JSON matching internal spec', () => {
    const jsonStr = generateManifestJson(sampleConfig);
    const parsed = JSON.parse(jsonStr);

    expect(parsed.schema_version).toBe('1.0.0');
    expect(parsed.experiment.task_type).toBe('classification');
    expect(parsed.experiment.metric).toBe('f1');
    expect(parsed.dataset.id).toBe('credit-risk-demo');
    expect(parsed.dataset.split.test_size).toBe(0.2);
    expect(parsed.dataset.split.seed).toBe(42);
    expect(parsed.model.adapter).toBe('random-forest-classifier');
    expect(parsed.model.parameters.n_estimators).toBe(100);
    expect(parsed.stress.type).toBe('gaussian_noise');
    expect(parsed.stress.severity_levels).toEqual([0.05, 0.1, 0.2, 0.3]);
  });
});
