import { Dataset } from '../schemas';

export const MOCK_DATASETS: Dataset[] = [
  {
    id: 'credit-risk-demo',
    name: 'Credit Risk Demo (synthetic)',
    description:
      'Synthetic credit default and risk benchmark dataset with calibrated non-linear decision boundaries.',
    sampleCount: 1000,
    featureCount: 4,
    classCount: 2,
    taskType: 'classification',
    isCustom: false,
    features: [
      { name: 'Credit Score', type: 'numeric', missingCount: 0 },
      { name: 'Income', type: 'numeric', missingCount: 0 },
      { name: 'Age', type: 'numeric', missingCount: 0 },
      { name: 'Loan Amount', type: 'numeric', missingCount: 0 },
    ],
  },
  {
    id: 'iris',
    name: 'Iris Flower Dataset',
    description:
      'Classic small multiclass botanical dataset for fast sanity checks and quick verification.',
    sampleCount: 150,
    featureCount: 4,
    classCount: 3,
    taskType: 'classification',
    isCustom: false,
    features: [
      { name: 'sepal_length', type: 'numeric', missingCount: 0 },
      { name: 'sepal_width', type: 'numeric', missingCount: 0 },
      { name: 'petal_length', type: 'numeric', missingCount: 0 },
      { name: 'petal_width', type: 'numeric', missingCount: 0 },
    ],
  },
  {
    id: 'housing-prices',
    name: 'Housing Price Dataset',
    description:
      'Continuous real estate evaluation dataset with median price targets for regression testing.',
    sampleCount: 506,
    featureCount: 13,
    taskType: 'regression',
    isCustom: false,
    features: [
      { name: 'crime_rate', type: 'numeric', missingCount: 0 },
      { name: 'avg_rooms', type: 'numeric', missingCount: 0 },
      { name: 'property_tax', type: 'numeric', missingCount: 0 },
      { name: 'median_price', type: 'numeric', missingCount: 0 },
    ],
  },
  {
    id: 'messy-census',
    name: 'Census Income (Messy Demo)',
    description:
      'Census dataset featuring missing entries and class imbalance for missingness stress testing.',
    sampleCount: 3200,
    featureCount: 12,
    classCount: 2,
    taskType: 'classification',
    isCustom: false,
    features: [
      { name: 'age', type: 'numeric', missingCount: 45 },
      { name: 'workclass', type: 'categorical', missingCount: 180 },
      { name: 'education', type: 'categorical', missingCount: 0 },
      { name: 'hours_per_week', type: 'numeric', missingCount: 12 },
    ],
  },
];
