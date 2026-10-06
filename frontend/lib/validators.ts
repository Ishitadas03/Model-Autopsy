import { z } from 'zod';
import { WorkspaceConfig } from './yaml';

export const Step1Schema = z.object({
  datasetId: z.string().min(1, 'Please select a dataset to continue'),
  datasetName: z.string().min(1),
  taskType: z.enum(['classification', 'regression']),
});

export const Step2Schema = z.object({
  modelId: z.string().min(1, 'Please select a model adapter to continue'),
  modelName: z.string().min(1),
});

export const Step3Schema = z.object({
  testSize: z
    .number()
    .min(0.05, 'Test size must be at least 5% (0.05)')
    .max(0.5, 'Test size must not exceed 50% (0.50)'),
  seed: z.number().int().min(0, 'Random seed must be a non-negative integer'),
});

export const Step4Schema = z
  .object({
    stressType: z.enum(['gaussian_noise', 'missingness'], {
      errorMap: () => ({
        message: 'Only Gaussian Noise and Missingness are currently available.',
      }),
    }),
    severityLevels: z
      .array(z.number())
      .min(1, 'At least one severity level is required')
      .refine(
        (levels) => levels.every((lvl) => lvl >= 0.05 && lvl <= 0.3),
        'Severity levels must be between 5% (0.05) and 30% (0.30)'
      ),
    stressMode: z.enum(['random', 'feature_specific', 'structured']),
    targetFeatures: z.array(z.string()).optional(),
    metric: z.string().min(1, 'Please select an evaluation metric'),
    failureThreshold: z.number(),
  })
  .superRefine((data, ctx) => {
    if (data.stressMode === 'feature_specific') {
      if (!data.targetFeatures || data.targetFeatures.length === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Select at least one feature for feature-specific perturbation.',
          path: ['targetFeatures'],
        });
      }
    }
  });

export function validateStep(
  step: 1 | 2 | 3 | 4 | 5,
  config: Partial<WorkspaceConfig>
): { isValid: boolean; error?: string } {
  if (step === 1) {
    const res = Step1Schema.safeParse(config);
    return {
      isValid: res.success,
      error: res.success ? undefined : res.error.errors[0]?.message,
    };
  }
  if (step === 2) {
    const res = Step2Schema.safeParse(config);
    return {
      isValid: res.success,
      error: res.success ? undefined : res.error.errors[0]?.message,
    };
  }
  if (step === 3) {
    const res = Step3Schema.safeParse(config);
    return {
      isValid: res.success,
      error: res.success ? undefined : res.error.errors[0]?.message,
    };
  }
  if (step === 4) {
    const res = Step4Schema.safeParse(config);
    return {
      isValid: res.success,
      error: res.success ? undefined : res.error.errors[0]?.message,
    };
  }
  return { isValid: true };
}
