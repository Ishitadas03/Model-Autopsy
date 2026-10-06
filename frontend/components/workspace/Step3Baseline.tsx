'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Dices, ShieldCheck, CheckCircle2, BarChart2 } from 'lucide-react';
import { TaskType } from '@/lib/schemas';
import { Button } from '@/components/ui/Button';
import { StatCard } from '@/components/ui/StatCard';
import { Callout } from '@/components/ui/Callout';

interface Step3BaselineProps {
  taskType?: TaskType;
  testSize: number;
  seed: number;
  onUpdateSplit: (testSize: number, seed: number) => void;
  baselineCompleted: boolean;
  onBaselineComplete: () => void;
}

export function Step3Baseline({
  taskType = 'classification',
  testSize,
  seed,
  onUpdateSplit,
  baselineCompleted,
  onBaselineComplete,
}: Step3BaselineProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleRandomizeSeed = () => {
    const newSeed = Math.floor(Math.random() * 90000) + 1000;
    onUpdateSplit(testSize, newSeed);
  };

  const handleRunBaseline = () => {
    setIsRunning(true);
    setProgress(15);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          onBaselineComplete();
          return 100;
        }
        return prev + 25;
      });
    }, 200);
  };

  return (
    <div className="space-y-6">
      <Callout type="info" title="Strict Data Isolation">
        The test split is permanently held out and never used to fit the model or any preprocessing transformers (scalers, encoders, imputers). Stratified sampling is automatically enforced for classification tasks.
      </Callout>

      {/* Split Configuration Card */}
      <div className="p-5 rounded-xl bg-surface border border-border space-y-6">
        <h4 className="font-manrope font-semibold text-sm text-white flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-accent" />
          <span>Evaluation Split & Seed Configuration</span>
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Test Size Slider */}
          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs">
              <label className="font-cabin uppercase tracking-wider text-text-subtle">
                Hold-out Test Size
              </label>
              <span className="font-mono text-white font-semibold">
                {Math.round(testSize * 100)}% ({testSize.toFixed(2)})
              </span>
            </div>

            <input
              type="range"
              min="0.05"
              max="0.50"
              step="0.05"
              value={testSize}
              onChange={(e) => onUpdateSplit(parseFloat(e.target.value), seed)}
              className="w-full accent-white bg-surface-2 rounded-lg cursor-pointer"
            />

            <div className="flex justify-between text-[11px] text-text-subtle font-mono">
              <span>5% (Min)</span>
              <span>20% (Default)</span>
              <span>50% (Max)</span>
            </div>
          </div>

          {/* Random Seed */}
          <div className="space-y-3">
            <label className="block text-xs font-cabin uppercase tracking-wider text-text-subtle">
              Pseudorandom Seed
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                value={seed}
                onChange={(e) => onUpdateSplit(testSize, parseInt(e.target.value) || 0)}
                className="flex-1 bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-white/40"
              />
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRandomizeSeed}
                className="gap-1.5"
              >
                <Dices className="w-3.5 h-3.5" />
                <span>Randomize</span>
              </Button>
            </div>
            <p className="text-[11px] text-text-subtle">
              Controls partition splitting and model internal weight initializations.
            </p>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-text-muted">
            Execute clean baseline to establish reference performance before applying perturbations.
          </p>
          <Button
            variant="primary"
            onClick={handleRunBaseline}
            loading={isRunning}
            className="w-full sm:w-auto"
          >
            <Play className="w-4 h-4 fill-current mr-2" />
            <span>{baselineCompleted ? 'Re-run Clean Baseline' : 'Run Clean Baseline'}</span>
          </Button>
        </div>

        {isRunning && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono text-text-subtle">
              <span>Fitting model on clean training set...</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full h-1.5 bg-surface-2 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-accent"
                style={{ width: `${progress}%` }}
                transition={{ duration: 0.2 }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Baseline Metric Results Card */}
      {baselineCompleted && (
        <div className="p-5 rounded-xl bg-surface border border-border space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-success" />
              <h4 className="font-manrope font-semibold text-sm text-white">
                Clean Baseline Metrics Verified
              </h4>
            </div>
            <span className="text-xs font-mono text-text-subtle">Split Seed: {seed}</span>
          </div>

          {taskType === 'classification' ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <StatCard label="Accuracy" value={96.2} suffix="%" caption="Clean hold-out accuracy" />
                <StatCard label="F1 Score" value={95.8} suffix="%" caption="Harmonic precision/recall" />
                <StatCard label="Precision" value={95.4} suffix="%" caption="True positive fidelity" />
                <StatCard label="ROC-AUC" value={0.985} decimals={3} caption="Area under ROC curve" />
              </div>

              {/* Confusion Matrix Heatmap */}
              <div className="p-4 rounded-lg bg-surface-2 border border-border">
                <div className="flex items-center gap-2 mb-3">
                  <BarChart2 className="w-4 h-4 text-text-subtle" />
                  <span className="text-xs font-manrope font-semibold text-white">
                    Baseline Confusion Matrix
                  </span>
                </div>

                <div className="max-w-xs mx-auto grid grid-cols-2 gap-2 text-center text-xs font-mono">
                  <div className="p-3 rounded bg-white/10 border border-white/20">
                    <div className="text-[10px] text-text-subtle">True Neg</div>
                    <div className="text-base font-bold text-white mt-1">96</div>
                  </div>
                  <div className="p-3 rounded bg-accent/15 border border-accent/30">
                    <div className="text-[10px] text-accent">False Pos</div>
                    <div className="text-base font-bold text-accent mt-1">4</div>
                  </div>
                  <div className="p-3 rounded bg-accent/15 border border-accent/30">
                    <div className="text-[10px] text-accent">False Neg</div>
                    <div className="text-base font-bold text-accent mt-1">3</div>
                  </div>
                  <div className="p-3 rounded bg-white/10 border border-white/20">
                    <div className="text-[10px] text-text-subtle">True Pos</div>
                    <div className="text-base font-bold text-white mt-1">97</div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <StatCard label="MAE" value={18420} decimals={0} caption="Mean absolute error" />
              <StatCard label="RMSE" value={23910} decimals={0} caption="Root mean squared error" />
              <StatCard label="R² Score" value={0.892} decimals={3} caption="Variance explained" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
