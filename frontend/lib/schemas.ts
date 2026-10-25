import { z } from 'zod';

export const TaskTypeSchema = z.enum(['classification', 'regression']);
export type TaskType = z.infer<typeof TaskTypeSchema>;

export const MetricTypeSchema = z.enum([
  'accuracy',
  'f1',
  'precision',
  'recall',
  'roc_auc',
  'pr_auc',
  'r2',
  'mae',
  'rmse',
  'loss',
]);
export type MetricType = z.infer<typeof MetricTypeSchema>;

export const StressTypeSchema = z.enum([
  'gaussian_noise',
  'missingness',
  'outliers',
  'feature_corruption',
  'distribution_shift',
]);
export type StressType = z.infer<typeof StressTypeSchema>;

export const RunStatusSchema = z.enum([
  'draft',
  'queued',
  'running',
  'completed',
  'failed',
  'cancelled',
]);
export type RunStatus = z.infer<typeof RunStatusSchema>;

export const DatasetFeatureSchema = z.object({
  name: z.string(),
  type: z.enum(['numeric', 'categorical', 'boolean']),
  missingCount: z.number().default(0),
});
export type DatasetFeature = z.infer<typeof DatasetFeatureSchema>;

export const DatasetSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  sampleCount: z.number(),
  featureCount: z.number(),
  classCount: z.number().optional(),
  taskType: TaskTypeSchema,
  isCustom: z.boolean().default(false),
  features: z.array(DatasetFeatureSchema),
});
export type Dataset = z.infer<typeof DatasetSchema>;

export const ModelAdapterSchema = z.object({
  id: z.string(),
  name: z.string(),
  framework: z.literal('scikit-learn'),
  taskTypes: z.array(TaskTypeSchema),
  predictProba: z.boolean(),
  description: z.string(),
  parameters: z.record(z.any()),
});
export type ModelAdapter = z.infer<typeof ModelAdapterSchema>;

export const StressConfigSchema = z.object({
  type: StressTypeSchema,
  severityLevels: z.array(z.number()),
  mode: z.enum(['random', 'feature_specific', 'structured']).default('random'),
  targetFeatures: z.array(z.string()).optional(),
});
export type StressConfig = z.infer<typeof StressConfigSchema>;

export const StatisticalValidationSchema = z.object({
  numSeeds: z.number(),
  mean: z.number(),
  std: z.number(),
  ci95: z.number(), // ± percentage / value
});
export type StatisticalValidation = z.infer<typeof StatisticalValidationSchema>;

export const ExperimentResultsSchema = z.object({
  baselineMetrics: z.record(z.number()),
  worstCaseMetrics: z.record(z.number()),
  failureThreshold: z.number(),
  observedBoundary: z.number().nullable(),
  observedBoundaryLabel: z.string().default(
    'Observed failure boundary under the specified experimental configuration.'
  ),
  failedSamplesCount: z.number(),
  statisticalValidation: StatisticalValidationSchema.optional(),
  mostVulnerableFeature: z
    .object({
      name: z.string(),
      degradationPp: z.number().optional(),
      relativeChangePercent: z.number(),
      caveat: z.string().default('Empirical sensitivity — not a causal explanation.'),
    })
    .optional(),
  curveData: z.array(
    z.object({
      severity: z.number(),
      f1: z.number().optional(),
      accuracy: z.number().optional(),
      mae: z.number().optional(),
      rmse: z.number().optional(),
      baseline: z.number(),
      threshold: z.number(),
    })
  ),
});
export type ExperimentResults = z.infer<typeof ExperimentResultsSchema>;

export const ExperimentSchema = z.object({
  id: z.string(),
  title: z.string(),
  datasetId: z.string(),
  datasetName: z.string(),
  modelId: z.string(),
  modelName: z.string(),
  taskType: TaskTypeSchema,
  stressConfig: StressConfigSchema,
  metric: MetricTypeSchema,
  failureThreshold: z.number(),
  testSize: z.number().min(0.05).max(0.5).default(0.2),
  seed: z.number().default(42),
  numSeeds: z.number().default(1),
  status: RunStatusSchema,
  createdAt: z.string(),
  completedAt: z.string().optional(),
  progressPercent: z.number().min(0).max(100).default(0),
  results: ExperimentResultsSchema.optional(),
  errorMessage: z.string().optional(),
});
export type Experiment = z.infer<typeof ExperimentSchema>;

export const FailedSampleSchema = z.object({
  id: z.string(),
  sampleIndex: z.number(),
  trueLabel: z.union([z.string(), z.number()]),
  predictedLabel: z.union([z.string(), z.number()]),
  confidence: z.number(),
  stressType: StressTypeSchema,
  severity: z.number(),
  features: z.record(
    z.object({
      clean: z.number(),
      stressed: z.number(),
    })
  ),
});
export type FailedSample = z.infer<typeof FailedSampleSchema>;

// ==========================================
// E003 Multi-Model Robustness Comparison Schemas
// ==========================================

export const MetricStatisticsSchema = z.object({
  n: z.number(),
  mean: z.number(),
  sample_std: z.number(),
  sem: z.number(),
  df: z.number(),
  t_critical: z.number(),
  margin_of_error: z.number(),
  ci_lower: z.number(),
  ci_upper: z.number(),
});
export type MetricStatistics = z.infer<typeof MetricStatisticsSchema>;

export const SeverityAggregatePointSchema = z.object({
  severity: z.number(),
  n_successful_runs: z.number(),
  n_failed_runs: z.number(),
  macro_f1: MetricStatisticsSchema,
  accuracy: MetricStatisticsSchema,
  absolute_degradation_pp: MetricStatisticsSchema,
  relative_degradation_pct: MetricStatisticsSchema,
  failure_count: z.number(),
  failure_proportion: z.number(),
  is_mean_failed: z.boolean(),
});
export type SeverityAggregatePoint = z.infer<typeof SeverityAggregatePointSchema>;

export const CorruptionAggregateResultSchema = z.object({
  experiment_id: z.string(),
  seeds: z.array(z.number()),
  severities: z.array(z.number()),
  failure_threshold: z.number(),
  n_total_seeds: z.number(),
  n_successful_seeds: z.number(),
  n_failed_seeds: z.number(),
  failed_seed_details: z.array(z.any()).default([]),
  per_seed_boundaries: z.record(z.number().nullable()).optional(),
  severity_aggregates: z.array(SeverityAggregatePointSchema),
  mean_observed_boundary: z.number().nullable(),
  earliest_individual_boundary: z.number().nullable(),
  boundary_caption: z.string(),
  monotonicity_summary: z.record(z.any()).optional(),
});
export type CorruptionAggregateResult = z.infer<typeof CorruptionAggregateResultSchema>;

export const ModelComparisonDataSchema = z.object({
  corruptions: z.record(CorruptionAggregateResultSchema),
});
export type ModelComparisonData = z.infer<typeof ModelComparisonDataSchema>;

export const E003ComparisonDataSchema = z.object({
  experiment_id: z.string(),
  protocol_version: z.string(),
  timestamp_utc: z.string(),
  dataset_metadata: z.object({
    name: z.string(),
    n_total: z.number(),
    n_train: z.number(),
    n_test: z.number(),
    feature_names: z.array(z.string()),
    target_names: z.array(z.string()),
    feature_sigmas: z.array(z.number()).optional(),
    feature_means: z.array(z.number()).optional(),
    dataset_hash: z.string(),
    split_seed: z.number(),
  }),
  models_metadata: z.record(z.any()),
  seeds_config: z.object({
    split_seed: z.number(),
    research_seeds: z.array(z.number()),
  }),
  failure_threshold: z.number(),
  models: z.record(ModelComparisonDataSchema),
});
export type E003ComparisonData = z.infer<typeof E003ComparisonDataSchema>;

