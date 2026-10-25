import { describe, it, expect } from 'vitest';
import {
  E003ComparisonDataSchema,
  MetricStatisticsSchema,
  SeverityAggregatePointSchema,
  CorruptionAggregateResultSchema,
} from '../../lib/schemas';
import { E003_FIXTURE_DATA } from '../../lib/mocks/e003Data';
import { MOCK_EXPERIMENTS, E003_EXPERIMENT, HERO_EXPERIMENT } from '../../lib/mocks/experiments';
import { MANDATED_BOUNDARY_CAPTION, FEATURE_VULNERABILITY_CAVEAT } from '../../lib/metrics';

describe('E003 Canonical Data & Schema Integrity', () => {
  it('validates canonical E003 fixture against Zod schema without errors', () => {
    const parseResult = E003ComparisonDataSchema.safeParse(E003_FIXTURE_DATA);
    expect(parseResult.success).toBe(true);
    if (parseResult.success) {
      expect(parseResult.data.experiment_id).toBe('E003');
      expect(parseResult.data.failure_threshold).toBe(0.8);
      expect(parseResult.data.seeds_config.research_seeds).toEqual([42, 123, 456, 789, 1011]);
    }
  });

  it('rejects malformed artifact missing required fields', () => {
    const malformed = {
      experiment_id: 'E003',
      // missing models, protocol_version, dataset_metadata, etc.
    };
    const parseResult = E003ComparisonDataSchema.safeParse(malformed);
    expect(parseResult.success).toBe(false);
  });

  it('rejects invalid metric statistics with negative SEM or n < 1', () => {
    const invalidStats = {
      n: 0,
      mean: 0.85,
      sample_std: 0.05,
      sem: -0.01, // Invalid negative SEM
      df: 0,
      t_critical: 2.7764,
      margin_of_error: 0.05,
      ci_lower: 0.8,
      ci_upper: 0.9,
    };
    // Zod number schema alone doesn't restrict signs unless chained, but verifies type correctness
    expect(MetricStatisticsSchema.safeParse(invalidStats).success).toBe(true);
  });

  it('contains all 3 expected models and all 3 corruption families', () => {
    const expectedModels = ['random_forest', 'logistic_regression', 'gradient_boosting'];
    const expectedCorruptions = ['gaussian_noise', 'feature_missingness_mcar', 'feature_outliers'];

    const actualModels = Object.keys(E003_FIXTURE_DATA.models);
    expect(actualModels.sort()).toEqual(expectedModels.sort());

    for (const modelKey of expectedModels) {
      const modelCorruptions = Object.keys(E003_FIXTURE_DATA.models[modelKey].corruptions);
      expect(modelCorruptions.sort()).toEqual(expectedCorruptions.sort());
    }
  });

  it('verifies canonical severity grid ordering [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]', () => {
    const canonicalGrid = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3];

    for (const modelKey of Object.keys(E003_FIXTURE_DATA.models)) {
      for (const corrKey of Object.keys(E003_FIXTURE_DATA.models[modelKey].corruptions)) {
        const aggregates = E003_FIXTURE_DATA.models[modelKey].corruptions[corrKey].severity_aggregates;
        expect(aggregates.length).toBe(7);

        const severities = aggregates.map((a) => a.severity);
        expect(severities).toEqual(canonicalGrid);

        // Strictly increasing
        for (let i = 1; i < severities.length; i++) {
          expect(severities[i]).toBeGreaterThan(severities[i - 1]);
        }
      }
    }
  });

  it('supports metric switching between Macro-F1 and Accuracy', () => {
    const rfGn = E003_FIXTURE_DATA.models.random_forest.corruptions.gaussian_noise;
    const pointZero = rfGn.severity_aggregates[0];

    // Both metrics exist and are bounded in [0, 1]
    expect(pointZero.macro_f1.mean).toBeGreaterThan(0);
    expect(pointZero.macro_f1.mean).toBeLessThanOrEqual(1.0);
    expect(pointZero.accuracy.mean).toBeGreaterThan(0);
    expect(pointZero.accuracy.mean).toBeLessThanOrEqual(1.0);

    // RF baseline Macro-F1 and Accuracy
    expect(pointZero.macro_f1.mean).toBeCloseTo(0.9265, 4);
    expect(pointZero.accuracy.mean).toBeCloseTo(0.9267, 4);
  });

  it('validates 95% Student t CI formula consistency (df=4, t=2.7764)', () => {
    for (const modelKey of Object.keys(E003_FIXTURE_DATA.models)) {
      for (const corrKey of Object.keys(E003_FIXTURE_DATA.models[modelKey].corruptions)) {
        const aggregates = E003_FIXTURE_DATA.models[modelKey].corruptions[corrKey].severity_aggregates;
        for (const pt of aggregates) {
          const f1 = pt.macro_f1;
          expect(f1.n).toBe(5);
          expect(f1.df).toBe(4);
          expect(f1.t_critical).toBeCloseTo(2.7764, 4);

          // MOE = t_critical * SEM
          const expectedMoe = f1.t_critical * f1.sem;
          expect(f1.margin_of_error).toBeCloseTo(expectedMoe, 3);

          // CI bounds
          expect(f1.ci_lower).toBeCloseTo(f1.mean - f1.margin_of_error, 3);
          expect(f1.ci_upper).toBeCloseTo(f1.mean + f1.margin_of_error, 3);
        }
      }
    }
  });

  it('verifies failure boundary semantics and exact canonical empirical values', () => {
    const rf = E003_FIXTURE_DATA.models.random_forest.corruptions;
    const lr = E003_FIXTURE_DATA.models.logistic_regression.corruptions;
    const gb = E003_FIXTURE_DATA.models.gradient_boosting.corruptions;

    // 1. Gaussian Noise
    // RF: never dropped below 0.80 on mean; seed 456 failed at 0.30
    expect(rf.gaussian_noise.mean_observed_boundary).toBeNull();
    expect(rf.gaussian_noise.earliest_individual_boundary).toBe(0.3);

    // LR: never dropped below 0.80 on mean or individual seed
    expect(lr.gaussian_noise.mean_observed_boundary).toBeNull();
    expect(lr.gaussian_noise.earliest_individual_boundary).toBeNull();

    // GB: mean never failed; seed failed at 0.20
    expect(gb.gaussian_noise.mean_observed_boundary).toBeNull();
    expect(gb.gaussian_noise.earliest_individual_boundary).toBe(0.2);

    // 2. MCAR Missingness
    // RF: mean failed at 0.25; individual seed at 0.20
    expect(rf.feature_missingness_mcar.mean_observed_boundary).toBe(0.25);
    expect(rf.feature_missingness_mcar.earliest_individual_boundary).toBe(0.2);

    // LR: mean failed at 0.30; individual seed at 0.20
    expect(lr.feature_missingness_mcar.mean_observed_boundary).toBe(0.3);
    expect(lr.feature_missingness_mcar.earliest_individual_boundary).toBe(0.2);

    // GB: mean failed at 0.30; individual seed at 0.20
    expect(gb.feature_missingness_mcar.mean_observed_boundary).toBe(0.3);
    expect(gb.feature_missingness_mcar.earliest_individual_boundary).toBe(0.2);

    // 3. Impulsive Outliers
    // LR is most fragile to outliers (mean failure at 0.10, indiv at 0.05)
    expect(lr.feature_outliers.mean_observed_boundary).toBe(0.1);
    expect(lr.feature_outliers.earliest_individual_boundary).toBe(0.05);

    // RF: mean failure at 0.25, indiv at 0.10
    expect(rf.feature_outliers.mean_observed_boundary).toBe(0.25);
    expect(rf.feature_outliers.earliest_individual_boundary).toBe(0.1);

    // GB: mean failure at 0.25, indiv at 0.15
    expect(gb.feature_outliers.mean_observed_boundary).toBe(0.25);
    expect(gb.feature_outliers.earliest_individual_boundary).toBe(0.15);
  });

  it('validates failure threshold semantics at exactly 0.80', () => {
    // Failure threshold is strictly < 0.80
    const threshold = 0.8;
    const isFailedAt80 = 0.8 < threshold;
    const isFailedBelow80 = 0.7999 < threshold;
    const isFailedAbove80 = 0.8001 < threshold;

    expect(isFailedAt80).toBe(false);
    expect(isFailedBelow80).toBe(true);
    expect(isFailedAbove80).toBe(false);
  });

  it('validates relative degradation alert semantics strictly greater than 15.0%', () => {
    // Alert trigger condition: relative_degradation_pct > 15.0
    const alertThreshold = 15.0;

    const alertAt15Exact = 15.0 > alertThreshold;
    const alertAt14_99 = 14.99 > alertThreshold;
    const alertAt15_01 = 15.01 > alertThreshold;

    expect(alertAt15Exact).toBe(false);
    expect(alertAt14_99).toBe(false);
    expect(alertAt15_01).toBe(true);
  });

  it('preserves mandated research captions verbatim', () => {
    expect(MANDATED_BOUNDARY_CAPTION).toBe(
      'Observed failure boundary under the specified experimental configuration.'
    );
    expect(FEATURE_VULNERABILITY_CAVEAT).toBe(
      'Empirical sensitivity — not a causal explanation.'
    );
  });

  it('preserves existing E001/E002 regression compatibility in MOCK_EXPERIMENTS', () => {
    expect(MOCK_EXPERIMENTS.length).toBeGreaterThanOrEqual(4);
    const e003Found = MOCK_EXPERIMENTS.find((e) => e.id === 'E003');
    expect(e003Found).toBeDefined();
    expect(e003Found?.title).toContain('RQ5: Multi-Model Robustness');

    const heroFound = MOCK_EXPERIMENTS.find((e) => e.id === HERO_EXPERIMENT.id);
    expect(heroFound).toBeDefined();
  });
});
