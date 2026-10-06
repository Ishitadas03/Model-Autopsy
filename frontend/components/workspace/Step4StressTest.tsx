'use client';

import React from 'react';
import {
  AlertTriangle,
  Sparkles,
  Layers,
  Activity,
  Sliders,
  HelpCircle,
  Lock,
  Plus,
  Trash2,
} from 'lucide-react';
import { TaskType } from '@/lib/schemas';
import { Badge } from '@/components/ui/Badge';
import { Callout } from '@/components/ui/Callout';
import { Tooltip } from '@/components/ui/Tooltip';

interface Step4StressTestProps {
  taskType?: TaskType;
  datasetFeatures?: string[];
  stressType: string;
  severityLevels: number[];
  stressMode: 'random' | 'feature_specific' | 'structured';
  targetFeatures: string[];
  metric: string;
  failureThreshold: number;
  onUpdateStress: (updates: {
    stressType?: string;
    severityLevels?: number[];
    stressMode?: 'random' | 'feature_specific' | 'structured';
    targetFeatures?: string[];
    metric?: string;
    failureThreshold?: number;
  }) => void;
}

export function Step4StressTest({
  taskType = 'classification',
  datasetFeatures = ['Credit Score', 'Income', 'Age', 'Loan Amount'],
  stressType,
  severityLevels,
  stressMode,
  targetFeatures,
  metric,
  failureThreshold,
  onUpdateStress,
}: Step4StressTestProps) {
  const stressFamilies = [
    {
      id: 'gaussian_noise',
      name: 'Gaussian Noise',
      description: 'Zero-mean normal noise perturbation scaled by empirical feature standard deviation.',
      enabled: true,
      unit: '% of feature std-dev',
    },
    {
      id: 'missingness',
      name: 'Missingness Injection',
      description: 'Simulates MCAR/MAR dropouts by nullifying evaluation feature entries.',
      enabled: true,
      unit: '% missing values',
    },
    {
      id: 'outliers',
      name: 'Extreme Outliers',
      description: 'Injects heavy-tailed Cauchy/extreme value deviations to test outlier resistance.',
      enabled: false,
      badge: 'Coming soon',
    },
    {
      id: 'feature_corruption',
      name: 'Feature Corruption',
      description: 'Targeted column shuffling and high-leverage adversarial feature corruption.',
      enabled: false,
      badge: 'Coming soon',
    },
    {
      id: 'distribution_shift',
      name: 'Covariate Shift',
      description: 'Controlled domain shift via subpopulation reweighting and mean drift.',
      enabled: false,
      badge: 'Coming soon',
    },
  ];

  const metricsByTask =
    taskType === 'classification'
      ? [
          { id: 'f1', name: 'F1 Score', direction: 'higher' },
          { id: 'accuracy', name: 'Accuracy', direction: 'higher' },
          { id: 'precision', name: 'Precision', direction: 'higher' },
          { id: 'recall', name: 'Recall', direction: 'higher' },
          { id: 'roc_auc', name: 'ROC-AUC', direction: 'higher' },
        ]
      : [
          { id: 'mae', name: 'MAE (Mean Absolute Error)', direction: 'lower' },
          { id: 'rmse', name: 'RMSE (Root Mean Squared Error)', direction: 'lower' },
          { id: 'r2', name: 'R² Variance Explained', direction: 'higher' },
        ];

  const currentMetricObj = metricsByTask.find((m) => m.id === metric) || metricsByTask[0];
  const isLowerBetter = currentMetricObj.direction === 'lower';

  const handleAddSeverity = () => {
    if (severityLevels.length >= 6) return;
    const last = severityLevels[severityLevels.length - 1] || 0.1;
    const nextVal = Math.min(0.3, parseFloat((last + 0.05).toFixed(2)));
    if (!severityLevels.includes(nextVal)) {
      onUpdateStress({ severityLevels: [...severityLevels, nextVal].sort((a, b) => a - b) });
    }
  };

  const handleRemoveSeverity = (index: number) => {
    if (severityLevels.length <= 1) return;
    const updated = severityLevels.filter((_, i) => i !== index);
    onUpdateStress({ severityLevels: updated });
  };

  const handleUpdateSeverityVal = (index: number, val: number) => {
    const clamped = Math.max(0.05, Math.min(0.3, val));
    const copy = [...severityLevels];
    copy[index] = clamped;
    onUpdateStress({ severityLevels: copy.sort((a, b) => a - b) });
  };

  const toggleTargetFeature = (feat: string) => {
    const updated = targetFeatures.includes(feat)
      ? targetFeatures.filter((f) => f !== feat)
      : [...targetFeatures, feat];
    onUpdateStress({ targetFeatures: updated });
  };

  return (
    <div className="space-y-6">
      <Callout type="info" title="Evaluation-Only Stress Protocol">
        Stress is applied to evaluation inputs only. The model parameters and clean training baseline remain completely unaltered to measure empirical resilience.
      </Callout>

      {/* Stress Family Selector */}
      <div className="space-y-3">
        <label className="block text-xs font-cabin uppercase tracking-wider text-text-subtle">
          1. Choose Stress Family
        </label>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {stressFamilies.map((fam) => {
            const isSelected = stressType === fam.id;
            const isAvailable = fam.enabled;

            return (
              <div
                key={fam.id}
                role="button"
                tabIndex={isAvailable ? 0 : -1}
                onClick={() => isAvailable && onUpdateStress({ stressType: fam.id })}
                onKeyDown={(e) => {
                  if (isAvailable && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault();
                    onUpdateStress({ stressType: fam.id });
                  }
                }}
                className={`p-4 rounded-xl border transition-all text-left flex flex-col justify-between ${
                  !isAvailable
                    ? 'opacity-40 bg-surface/50 border-border cursor-not-allowed'
                    : isSelected
                    ? 'bg-surface-2 border-white ring-2 ring-white/20 shadow-lg cursor-pointer'
                    : 'bg-surface border-border hover:border-border-strong cursor-pointer'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="font-manrope font-semibold text-xs text-white">
                      {fam.name}
                    </span>
                    {!isAvailable ? (
                      <Badge variant="outline" className="text-[9px] text-text-subtle">
                        {fam.badge}
                      </Badge>
                    ) : (
                      <Badge variant="success" className="text-[9px]">
                        Available
                      </Badge>
                    )}
                  </div>
                  <p className="text-[11px] text-text-muted leading-relaxed line-clamp-2">
                    {fam.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Severity Levels Configuration */}
      <div className="p-5 rounded-xl bg-surface border border-border space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-manrope font-semibold text-xs text-white uppercase tracking-wider">
              2. Severity Increments ({stressType === 'gaussian_noise' ? 'Std Dev Fraction' : 'Missing %'})
            </h4>
            <p className="text-[11px] text-text-subtle mt-0.5">
              Allowed range: 5% (0.05) to 30% (0.30). At least one step required.
            </p>
          </div>

          <button
            type="button"
            onClick={handleAddSeverity}
            disabled={severityLevels.length >= 6}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/20 hover:border-white/50 text-xs font-cabin text-white disabled:opacity-40 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Level</span>
          </button>
        </div>

        {/* Chips */}
        <div className="flex flex-wrap gap-2.5 pt-2">
          {severityLevels.map((lvl, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-2 border border-border text-xs font-mono text-white"
            >
              <span>{Math.round(lvl * 100)}%</span>
              <button
                type="button"
                onClick={() => handleRemoveSeverity(idx)}
                disabled={severityLevels.length <= 1}
                className="text-text-subtle hover:text-accent disabled:opacity-20 transition-colors"
                title="Remove increment"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Perturbation Mode & Target Features */}
      <div className="p-5 rounded-xl bg-surface border border-border space-y-4">
        <h4 className="font-manrope font-semibold text-xs text-white uppercase tracking-wider">
          3. Perturbation Dispersion Mode
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { id: 'random', label: 'Random (Uniform)', desc: 'Applies noise across all features equally.' },
            { id: 'feature_specific', label: 'Feature-Specific', desc: 'Isolates vulnerability to selected columns.' },
            { id: 'structured', label: 'Structured / Correlated', desc: 'Preserves empirical covariance matrix.' },
          ].map((mode) => (
            <button
              key={mode.id}
              type="button"
              onClick={() => onUpdateStress({ stressMode: mode.id as any })}
              className={`p-3 rounded-lg border text-left transition-all ${
                stressMode === mode.id
                  ? 'bg-surface-2 border-white text-white'
                  : 'bg-surface-2/40 border-border text-text-muted hover:border-white/30'
              }`}
            >
              <div className="font-manrope font-semibold text-xs text-white">{mode.label}</div>
              <p className="text-[10px] text-text-subtle mt-1 leading-snug">{mode.desc}</p>
            </button>
          ))}
        </div>

        {stressMode === 'feature_specific' && (
          <div className="pt-2 space-y-2 border-t border-white/5">
            <span className="text-xs text-text-subtle font-cabin uppercase tracking-wider block">
              Select target features for perturbation:
            </span>
            <div className="flex flex-wrap gap-2">
              {datasetFeatures.map((feat) => {
                const isSelected = targetFeatures.includes(feat);
                return (
                  <button
                    key={feat}
                    type="button"
                    onClick={() => toggleTargetFeature(feat)}
                    className={`px-3 py-1 rounded-md text-xs font-mono transition-colors ${
                      isSelected
                        ? 'bg-accent/20 border border-accent/60 text-white'
                        : 'bg-surface-2 border border-border text-text-muted hover:text-white'
                    }`}
                  >
                    {feat}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Metric & Failure Threshold */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Metric selection */}
        <div className="p-5 rounded-xl bg-surface border border-border space-y-2">
          <label className="block text-xs font-cabin uppercase tracking-wider text-text-subtle">
            Primary Robustness Metric
          </label>
          <select
            value={metric}
            onChange={(e) => onUpdateStress({ metric: e.target.value })}
            className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-white/40"
          >
            {metricsByTask.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.direction === 'higher' ? 'Higher is better' : 'Lower is better'})
              </option>
            ))}
          </select>
          <p className="text-[11px] text-text-subtle">
            The curve and degradation will be computed strictly against this metric.
          </p>
        </div>

        {/* Failure Threshold */}
        <div className="p-5 rounded-xl bg-surface border border-border space-y-2">
          <label className="block text-xs font-cabin uppercase tracking-wider text-text-subtle">
            Failure Threshold Definition
          </label>
          <input
            type="number"
            step="0.05"
            value={failureThreshold}
            onChange={(e) =>
              onUpdateStress({ failureThreshold: parseFloat(e.target.value) || 0 })
            }
            className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-white/40"
          />
          <p className="text-[11px] text-accent font-medium">
            {isLowerBetter
              ? `Failure declared when ${metric.toUpperCase()} exceeds ${failureThreshold}.`
              : `Failure declared when ${metric.toUpperCase()} drops below ${failureThreshold}.`}
          </p>
        </div>
      </div>

      {/* Repeated Seeds / Uncertainty Control (Disabled research phase) */}
      <div className="p-4 rounded-xl bg-surface/50 border border-white/5 flex items-center justify-between text-xs opacity-60">
        <div className="flex items-center gap-2.5">
          <Lock className="w-4 h-4 text-text-subtle" />
          <div>
            <div className="font-semibold text-white">Repeated Seeds (Uncertainty Quantification)</div>
            <div className="text-[11px] text-text-subtle">
              Enables 95% Confidence Interval bootstrapping over repeated perturbation seeds.
            </div>
          </div>
        </div>
        <Badge variant="outline" className="text-[10px]">
          Research phase
        </Badge>
      </div>
    </div>
  );
}
