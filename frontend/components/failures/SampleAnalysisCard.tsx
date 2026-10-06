'use client';

import React, { useState } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Target, XCircle, CheckCircle2, Sliders, Layers, Sparkles } from 'lucide-react';
import { FailedSample } from '@/lib/schemas';
import { Badge } from '@/components/ui/Badge';

interface SampleAnalysisCardProps {
  sample: FailedSample | null;
}

export function SampleAnalysisCard({ sample }: SampleAnalysisCardProps) {
  const [xAxisFeature, setXAxisFeature] = useState<'Income' | 'Credit Score' | 'Age' | 'Loan Amount'>('Income');
  const [yAxisFeature, setYAxisFeature] = useState<'Income' | 'Credit Score' | 'Age' | 'Loan Amount'>('Credit Score');

  if (!sample) {
    return (
      <div className="bg-surface rounded-xl border border-border p-6 text-center text-text-subtle text-xs">
        Select a sample from the failure table to inspect feature perturbations and 2D decision geometry.
      </div>
    );
  }

  // Generate synthetic 2D decision boundary scatter points for background context
  const scatterPoints = [
    { x: 55000, y: 720, type: 'correct' },
    { x: 62000, y: 740, type: 'correct' },
    { x: 71000, y: 760, type: 'correct' },
    { x: 80000, y: 790, type: 'correct' },
    { x: 45000, y: 650, type: 'correct' },
    { x: 38000, y: 610, type: 'misclassified' },
    { x: 42000, y: 590, type: 'misclassified' },
    { x: 49000, y: 560, type: 'misclassified' },
    { x: 52000, y: 540, type: 'misclassified' },
    // Current sample point
    {
      x: sample.features[xAxisFeature]?.stressed || 58000,
      y: sample.features[yAxisFeature]?.stressed || 580,
      type: 'selected',
    },
  ];

  return (
    <div className="bg-surface rounded-xl border border-border shadow-xl p-5 space-y-5 sticky top-24 self-start">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-accent" />
          <h3 className="font-manrope font-semibold text-sm text-white">
            Sample Analysis — #{sample.sampleIndex}
          </h3>
        </div>
        <Badge variant="accent" className="text-[10px] font-mono">
          Misclassified
        </Badge>
      </div>

      {/* Axis feature pickers */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <label className="text-[10px] font-cabin uppercase text-text-subtle block mb-1">
            X-Axis Feature
          </label>
          <select
            value={xAxisFeature}
            onChange={(e) => setXAxisFeature(e.target.value as any)}
            className="w-full bg-surface-2 border border-border rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
          >
            <option value="Income">Income</option>
            <option value="Credit Score">Credit Score</option>
            <option value="Age">Age</option>
            <option value="Loan Amount">Loan Amount</option>
          </select>
        </div>

        <div>
          <label className="text-[10px] font-cabin uppercase text-text-subtle block mb-1">
            Y-Axis Feature
          </label>
          <select
            value={yAxisFeature}
            onChange={(e) => setYAxisFeature(e.target.value as any)}
            className="w-full bg-surface-2 border border-border rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
          >
            <option value="Credit Score">Credit Score</option>
            <option value="Income">Income</option>
            <option value="Loan Amount">Loan Amount</option>
            <option value="Age">Age</option>
          </select>
        </div>
      </div>

      {/* 2D Scatter Visualization */}
      <div className="space-y-2">
        <div className="h-48 w-full bg-surface-2/40 rounded-lg p-2 border border-border">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 10, right: 10, bottom: 5, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis
                type="number"
                dataKey="x"
                name={xAxisFeature}
                stroke="rgba(255,255,255,0.3)"
                fontSize={10}
                fontFamily="monospace"
              />
              <YAxis
                type="number"
                dataKey="y"
                name={yAxisFeature}
                stroke="rgba(255,255,255,0.3)"
                fontSize={10}
                fontFamily="monospace"
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{
                  backgroundColor: '#0c0c0f',
                  borderColor: 'rgba(255,255,255,0.15)',
                  borderRadius: '6px',
                  fontSize: '10px',
                  fontFamily: 'monospace',
                }}
              />
              <Scatter name="Samples" data={scatterPoints}>
                {scatterPoints.map((entry, index) => {
                  if (entry.type === 'selected') {
                    return (
                      <Cell
                        key={`cell-${index}`}
                        fill="#ef4444"
                        stroke="#ffffff"
                        strokeWidth={2}
                        r={6}
                      />
                    );
                  }
                  if (entry.type === 'misclassified') {
                    return <Cell key={`cell-${index}`} fill="#ef4444" r={3.5} />;
                  }
                  return <Cell key={`cell-${index}`} fill="rgba(255,255,255,0.3)" r={3} />;
                })}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between text-[10px] font-mono text-text-subtle pt-1">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-white/40" />
            <span>Correctly Predicted</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-accent" />
            <span>Misclassified</span>
          </span>
          <span className="flex items-center gap-1.5 text-accent font-semibold">
            <span className="w-2.5 h-2.5 rounded-full bg-accent ring-2 ring-white" />
            <span>Sample #{sample.sampleIndex}</span>
          </span>
        </div>
      </div>

      {/* Target & Prediction Meta */}
      <div className="grid grid-cols-2 gap-3 text-xs font-mono p-3 rounded-lg bg-surface-2 border border-border">
        <div>
          <span className="text-[10px] font-cabin uppercase text-text-subtle block">True Label</span>
          <span className="font-semibold text-white mt-0.5 block">{String(sample.trueLabel)}</span>
        </div>
        <div>
          <span className="text-[10px] font-cabin uppercase text-accent block">Predicted Label</span>
          <div className="flex items-center gap-1 font-semibold text-accent mt-0.5">
            <XCircle className="w-3.5 h-3.5" />
            <span>{String(sample.predictedLabel)}</span>
          </div>
        </div>
        <div>
          <span className="text-[10px] font-cabin uppercase text-text-subtle block">Confidence</span>
          <span className="text-white mt-0.5 block">{(sample.confidence * 100).toFixed(1)}%</span>
        </div>
        <div>
          <span className="text-[10px] font-cabin uppercase text-text-subtle block">Perturbation</span>
          <span className="text-accent mt-0.5 block">{Math.round(sample.severity * 100)}% Noise</span>
        </div>
      </div>

      {/* Feature Values (Stressed vs Clean) */}
      <div className="space-y-3 pt-2 border-t border-white/5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-cabin uppercase tracking-wider text-text-subtle">
            Feature Values (Stressed vs Clean)
          </span>
          <span className="text-[10px] font-mono text-text-subtle">Clean → Perturbed</span>
        </div>

        <div className="space-y-3">
          {Object.entries(sample.features).map(([featName, vals]) => {
            const clean = vals.clean;
            const stressed = vals.stressed;
            const diff = stressed - clean;

            return (
              <div key={featName} className="space-y-1 text-xs">
                <div className="flex justify-between items-center font-mono">
                  <span className="text-white text-[11px]">{featName}</span>
                  <span className="text-text-muted text-[10px]">
                    {clean.toLocaleString()} →{' '}
                    <span className={diff !== 0 ? 'text-accent font-semibold' : 'text-white'}>
                      {stressed.toLocaleString()}
                    </span>
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-surface-2 rounded-full overflow-hidden flex">
                    <div className="h-full bg-white/40" style={{ width: '45%' }} />
                    <div className="h-full bg-accent" style={{ width: '25%' }} />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
