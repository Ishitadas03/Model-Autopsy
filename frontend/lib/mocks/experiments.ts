import { Experiment, FailedSample } from '../schemas';
import { MANDATED_BOUNDARY_CAPTION, FEATURE_VULNERABILITY_CAVEAT } from '../metrics';

export const HERO_EXPERIMENT: Experiment = {
  id: 'EXP-0241',
  title: 'Random Forest Stress Test — Credit Risk Demo',
  datasetId: 'credit-risk-demo',
  datasetName: 'Credit Risk Demo (synthetic)',
  modelId: 'random-forest-classifier',
  modelName: 'Random Forest',
  taskType: 'classification',
  stressConfig: {
    type: 'gaussian_noise',
    severityLevels: [0.05, 0.1, 0.2, 0.3],
    mode: 'random',
  },
  metric: 'f1',
  failureThreshold: 0.8,
  testSize: 0.2,
  seed: 42,
  numSeeds: 5,
  status: 'completed',
  createdAt: '2026-10-04T14:30:00Z',
  completedAt: '2026-10-04T14:32:45Z',
  progressPercent: 100,
  results: {
    baselineMetrics: {
      f1: 0.958,
      accuracy: 0.962,
      precision: 0.954,
      recall: 0.962,
      roc_auc: 0.985,
    },
    worstCaseMetrics: {
      f1: 0.712,
      accuracy: 0.725,
      precision: 0.705,
      recall: 0.72,
      roc_auc: 0.792,
    },
    failureThreshold: 0.8,
    observedBoundary: 0.231, // 23.1%
    observedBoundaryLabel: MANDATED_BOUNDARY_CAPTION,
    failedSamplesCount: 143,
    statisticalValidation: {
      numSeeds: 5,
      mean: 0.712,
      std: 0.012,
      ci95: 0.024, // ± 2.4%
    },
    mostVulnerableFeature: {
      name: 'Credit Score',
      degradationPp: -28.4,
      relativeChangePercent: -29.6,
      caveat: FEATURE_VULNERABILITY_CAVEAT,
    },
    curveData: [
      { severity: 0, f1: 0.958, accuracy: 0.962, baseline: 0.958, threshold: 0.8 },
      { severity: 0.05, f1: 0.924, accuracy: 0.931, baseline: 0.958, threshold: 0.8 },
      { severity: 0.1, f1: 0.885, accuracy: 0.892, baseline: 0.958, threshold: 0.8 },
      { severity: 0.2, f1: 0.824, accuracy: 0.835, baseline: 0.958, threshold: 0.8 },
      { severity: 0.231, f1: 0.8, accuracy: 0.812, baseline: 0.958, threshold: 0.8 },
      { severity: 0.3, f1: 0.712, accuracy: 0.725, baseline: 0.958, threshold: 0.8 },
    ],
  },
};

export const IRIS_EXPERIMENT: Experiment = {
  id: 'EXP-0102',
  title: 'Logistic Regression × Iris Robustness',
  datasetId: 'iris',
  datasetName: 'Iris Flower Dataset',
  modelId: 'logistic-regression',
  modelName: 'Logistic Regression',
  taskType: 'classification',
  stressConfig: {
    type: 'gaussian_noise',
    severityLevels: [0.05, 0.1, 0.15, 0.2],
    mode: 'random',
  },
  metric: 'accuracy',
  failureThreshold: 0.85,
  testSize: 0.25,
  seed: 1337,
  numSeeds: 1, // Single seed — no uncertainty estimate
  status: 'completed',
  createdAt: '2026-10-03T11:00:00Z',
  completedAt: '2026-10-03T11:01:10Z',
  progressPercent: 100,
  results: {
    baselineMetrics: {
      accuracy: 0.967,
      f1: 0.967,
      precision: 0.97,
      recall: 0.967,
    },
    worstCaseMetrics: {
      accuracy: 0.833,
      f1: 0.831,
      precision: 0.84,
      recall: 0.833,
    },
    failureThreshold: 0.85,
    observedBoundary: 0.182,
    observedBoundaryLabel: MANDATED_BOUNDARY_CAPTION,
    failedSamplesCount: 5,
    curveData: [
      { severity: 0, accuracy: 0.967, baseline: 0.967, threshold: 0.85 },
      { severity: 0.05, accuracy: 0.933, baseline: 0.967, threshold: 0.85 },
      { severity: 0.1, accuracy: 0.9, baseline: 0.967, threshold: 0.85 },
      { severity: 0.15, accuracy: 0.867, baseline: 0.967, threshold: 0.85 },
      { severity: 0.2, accuracy: 0.833, baseline: 0.967, threshold: 0.85 },
    ],
  },
};

export const FAILED_EXPERIMENT: Experiment = {
  id: 'EXP-0089',
  title: 'Gradient Boosting × Housing Price Regression',
  datasetId: 'housing-prices',
  datasetName: 'Housing Price Dataset',
  modelId: 'gradient-boosting-regressor',
  modelName: 'Gradient Boosting Regressor',
  taskType: 'regression',
  stressConfig: {
    type: 'outliers',
    severityLevels: [0.05, 0.1, 0.2],
    mode: 'random',
  },
  metric: 'mae',
  failureThreshold: 45000,
  testSize: 0.2,
  seed: 99,
  numSeeds: 1,
  status: 'failed',
  createdAt: '2026-10-02T09:12:00Z',
  progressPercent: 42,
  errorMessage: 'Loss diverged to NaN during stress evaluation at 10% outlier severity.',
};

export const DRAFT_EXPERIMENT: Experiment = {
  id: 'EXP-0242',
  title: 'SVM Classifier × Credit Risk Demo',
  datasetId: 'credit-risk-demo',
  datasetName: 'Credit Risk Demo (synthetic)',
  modelId: 'svm-classifier',
  modelName: 'Support Vector Machine',
  taskType: 'classification',
  stressConfig: {
    type: 'missingness',
    severityLevels: [0.05, 0.1, 0.15],
    mode: 'random',
  },
  metric: 'f1',
  failureThreshold: 0.8,
  testSize: 0.2,
  seed: 42,
  numSeeds: 1,
  status: 'draft',
  createdAt: '2026-10-05T08:00:00Z',
  progressPercent: 0,
};

export const MOCK_EXPERIMENTS: Experiment[] = [
  HERO_EXPERIMENT,
  IRIS_EXPERIMENT,
  FAILED_EXPERIMENT,
  DRAFT_EXPERIMENT,
];

// Generate 143 realistic failed samples for EXP-0241
export const MOCK_FAILED_SAMPLES: FailedSample[] = Array.from({ length: 143 }, (_, i) => {
  const isHighSeverity = i % 2 === 0;
  const severity = isHighSeverity ? 0.3 : 0.2;
  const trueLabel = i % 3 === 0 ? 'Fraud' : 'Normal';
  const predictedLabel = trueLabel === 'Fraud' ? 'Normal' : 'Fraud';
  const confidence = 0.51 + ((i * 7) % 40) / 100;

  return {
    id: `sample-${i + 1}`,
    sampleIndex: 100 + i * 3,
    trueLabel,
    predictedLabel,
    confidence,
    stressType: 'gaussian_noise',
    severity,
    features: {
      'Credit Score': {
        clean: 680 + ((i * 13) % 140) - 70,
        stressed: 580 + ((i * 17) % 140) - 70,
      },
      Income: {
        clean: 65000 + ((i * 1900) % 50000),
        stressed: 59000 + ((i * 2100) % 50000),
      },
      Age: {
        clean: 25 + (i % 45),
        stressed: 26 + (i % 45),
      },
      'Loan Amount': {
        clean: 18000 + ((i * 850) % 25000),
        stressed: 21000 + ((i * 920) % 25000),
      },
    },
  };
});
