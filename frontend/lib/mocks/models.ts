import { ModelAdapter } from '../schemas';

export const MOCK_MODELS: ModelAdapter[] = [
  {
    id: 'logistic-regression',
    name: 'Logistic Regression',
    framework: 'scikit-learn',
    taskTypes: ['classification'],
    predictProba: true,
    description: 'Linear model for classification with calibrated probability estimates.',
    parameters: {
      C: 1.0,
      penalty: 'l2',
      max_iter: 100,
    },
  },
  {
    id: 'random-forest-classifier',
    name: 'Random Forest Classifier',
    framework: 'scikit-learn',
    taskTypes: ['classification'],
    predictProba: true,
    description: 'Ensemble of decision trees with feature bagging and out-of-bag scoring.',
    parameters: {
      n_estimators: 100,
      max_depth: 10,
      min_samples_split: 2,
    },
  },
  {
    id: 'gradient-boosting-classifier',
    name: 'Gradient Boosting Classifier',
    framework: 'scikit-learn',
    taskTypes: ['classification'],
    predictProba: true,
    description: 'Sequential boosting with gradient-based loss minimization.',
    parameters: {
      n_estimators: 100,
      learning_rate: 0.1,
      max_depth: 3,
    },
  },
  {
    id: 'svm-classifier',
    name: 'Support Vector Machine (SVC)',
    framework: 'scikit-learn',
    taskTypes: ['classification'],
    predictProba: false, // SVM caveat about confidence/probability calibration
    description: 'Maximum-margin hyperplane classifier with non-linear RBF kernel.',
    parameters: {
      C: 1.0,
      kernel: 'rbf',
      gamma: 'scale',
    },
  },
  {
    id: 'linear-regression',
    name: 'Linear Regression',
    framework: 'scikit-learn',
    taskTypes: ['regression'],
    predictProba: false,
    description: 'Ordinary least squares linear regression model.',
    parameters: {
      fit_intercept: true,
    },
  },
  {
    id: 'random-forest-regressor',
    name: 'Random Forest Regressor',
    framework: 'scikit-learn',
    taskTypes: ['regression'],
    predictProba: false,
    description: 'Ensemble of regression trees for non-linear target estimation.',
    parameters: {
      n_estimators: 100,
      max_depth: 12,
    },
  },
  {
    id: 'gradient-boosting-regressor',
    name: 'Gradient Boosting Regressor',
    framework: 'scikit-learn',
    taskTypes: ['regression'],
    predictProba: false,
    description: 'Iterative residual booster minimizing mean squared error.',
    parameters: {
      n_estimators: 100,
      learning_rate: 0.1,
      max_depth: 4,
    },
  },
];
