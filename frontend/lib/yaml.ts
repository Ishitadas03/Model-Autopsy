export interface WorkspaceConfig {
  datasetId?: string;
  datasetName?: string;
  taskType?: 'classification' | 'regression';
  modelId?: string;
  modelName?: string;
  modelParams?: Record<string, any>;
  testSize: number;
  seed: number;
  numSeeds: number;
  stressType: string;
  severityLevels: number[];
  stressMode: 'random' | 'feature_specific' | 'structured';
  targetFeatures?: string[];
  metric: string;
  failureThreshold: number;
}

export function generateExperimentYaml(config: WorkspaceConfig): string {
  const lines: string[] = [
    '# Model Autopsy Experiment Specification',
    '# Generated via Autopsy Workspace',
    'version: "1.0"',
    '',
    'experiment:',
    `  title: "${config.modelName || 'Model'} Stress Test — ${config.datasetName || 'Dataset'}"`,
    `  task_type: ${config.taskType || 'classification'}`,
    '',
    'dataset:',
    `  id: "${config.datasetId || 'custom'}"`,
    `  name: "${config.datasetName || 'Custom Dataset'}"`,
    '  split:',
    `    test_size: ${config.testSize.toFixed(2)}`,
    `    seed: ${config.seed}`,
    `    stratify: ${config.taskType === 'classification'}`,
    '',
    'model:',
    `  adapter: "${config.modelId || 'unselected'}"`,
    '  framework: "scikit-learn"',
    '  parameters:',
  ];

  if (config.modelParams && Object.keys(config.modelParams).length > 0) {
    for (const [k, v] of Object.entries(config.modelParams)) {
      lines.push(`    ${k}: ${JSON.stringify(v)}`);
    }
  } else {
    lines.push('    {}');
  }

  lines.push('');
  lines.push('stress_test:');
  lines.push(`  type: ${config.stressType}`);
  lines.push(`  mode: ${config.stressMode}`);
  lines.push(`  severity_levels: [${config.severityLevels.map((s) => s.toFixed(2)).join(', ')}]`);
  if (config.targetFeatures && config.targetFeatures.length > 0) {
    lines.push(`  target_features: [${config.targetFeatures.map((f) => `"${f}"`).join(', ')}]`);
  }
  lines.push(`  metric: ${config.metric}`);
  lines.push(`  failure_threshold: ${config.failureThreshold}`);
  lines.push(`  num_seeds: ${config.numSeeds}`);
  lines.push('');
  lines.push('metadata:');
  lines.push('  platform: "Model Autopsy"');
  lines.push('  spec_version: "2026.1"');
  lines.push(`  created_at: "${new Date().toISOString()}"`);

  return lines.join('\n');
}

export function generateManifestJson(config: WorkspaceConfig): string {
  return JSON.stringify(
    {
      schema_version: '1.0.0',
      created_at: new Date().toISOString(),
      experiment: {
        task_type: config.taskType || 'classification',
        metric: config.metric,
        failure_threshold: config.failureThreshold,
      },
      dataset: {
        id: config.datasetId,
        name: config.datasetName,
        split: {
          test_size: config.testSize,
          seed: config.seed,
        },
      },
      model: {
        adapter: config.modelId,
        framework: 'scikit-learn',
        parameters: config.modelParams || {},
      },
      stress: {
        type: config.stressType,
        mode: config.stressMode,
        severity_levels: config.severityLevels,
        target_features: config.targetFeatures || [],
        num_seeds: config.numSeeds,
      },
      runtime: {
        platform: 'model-autopsy-engine',
        reproducible: true,
      },
    },
    null,
    2
  );
}
