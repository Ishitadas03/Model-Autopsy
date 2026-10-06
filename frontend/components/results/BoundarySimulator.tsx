'use client';

import React, { useState } from 'react';
import { Compass, HelpCircle, AlertOctagon } from 'lucide-react';
import { MANDATED_BOUNDARY_CAPTION } from '@/lib/metrics';
import { Badge } from '@/components/ui/Badge';

interface BoundarySimulatorProps {
  initialThreshold?: number;
  curveData?: { severity: number; score: number }[];
  isLowerBetter?: boolean;
}

const DEFAULT_CURVE = [
  { severity: 0, score: 0.958 },
  { severity: 0.05, score: 0.924 },
  { severity: 0.1, score: 0.885 },
  { severity: 0.2, score: 0.824 },
  { severity: 0.3, score: 0.712 },
];

/**
 * Calculates failure boundary via linear interpolation between tested severities.
 */
export function computeBoundary(
  threshold: number,
  points: { severity: number; score: number }[] = DEFAULT_CURVE,
  isLowerBetter = false
): number | null {
  for (let i = 0; i < points.length - 1; i++) {
    const p1 = points[i];
    const p2 = points[i + 1];

    const crosses = isLowerBetter
      ? p1.score <= threshold && p2.score >= threshold
      : p1.score >= threshold && p2.score <= threshold;

    if (crosses) {
      if (p2.score === p1.score) return p1.severity;
      const ratio = (threshold - p1.score) / (p2.score - p1.score);
      return parseFloat((p1.severity + ratio * (p2.severity - p1.severity)).toFixed(3));
    }
  }

  return null;
}

export function BoundarySimulator({
  initialThreshold = 0.8,
  curveData = DEFAULT_CURVE,
  isLowerBetter = false,
}: BoundarySimulatorProps) {
  const [threshold, setThreshold] = useState<number>(initialThreshold);

  const boundary = computeBoundary(threshold, curveData, isLowerBetter);
  const boundaryText =
    boundary !== null ? `≈ ${(boundary * 100).toFixed(1)}%` : 'Not reached within tested range';

  return (
    <div className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-accent" />
          <h3 className="font-manrope font-semibold text-sm text-white">
            Interactive Failure Boundary Simulator
          </h3>
        </div>
        <Badge variant="outline" className="text-[10px] font-mono">
          Linear Interpolation
        </Badge>
      </div>

      <p className="text-xs text-text-muted leading-relaxed">
        Dynamically adjust the failure definition threshold to compute the precise perturbation magnitude where model resilience collapses below operational specifications.
      </p>

      {/* Threshold Slider */}
      <div className="space-y-3 p-4 rounded-lg bg-surface-2 border border-border">
        <div className="flex items-center justify-between text-xs">
          <label className="font-cabin uppercase tracking-wider text-text-subtle">
            Failure Threshold Definition (Metric: F1)
          </label>
          <span className="font-mono text-white font-bold text-sm">
            {threshold.toFixed(2)}
          </span>
        </div>

        <input
          type="range"
          min="0.70"
          max="0.95"
          step="0.01"
          value={threshold}
          onChange={(e) => setThreshold(parseFloat(e.target.value))}
          className="w-full accent-accent bg-surface rounded-lg cursor-pointer"
        />

        <div className="flex justify-between text-[11px] text-text-subtle font-mono">
          <span>0.70 (Permissive)</span>
          <span>0.80 (Default)</span>
          <span>0.95 (Strict)</span>
        </div>
      </div>

      {/* Computed Result Box */}
      <div className="p-5 rounded-lg bg-surface-2/60 border border-white/10 space-y-2">
        <span className="text-[10px] font-cabin uppercase text-text-subtle tracking-wider block">
          Computed Observed Boundary
        </span>
        <div className="font-manrope font-bold text-3xl text-white tabular-nums">
          {boundaryText}
        </div>

        {/* Mandated Caption verbatim */}
        <p className="text-xs text-text-subtle italic pt-2 border-t border-white/5">
          {MANDATED_BOUNDARY_CAPTION}
        </p>
      </div>

      {/* Methodology note */}
      <div className="text-[11px] text-text-subtle leading-relaxed flex items-start gap-2">
        <HelpCircle className="w-4 h-4 text-text-subtle flex-shrink-0 mt-0.5" />
        <span>
          <strong>Methodology:</strong> Calculated via 1D linear piecewise interpolation across empirical evaluation checkpoints: 0%, 5%, 10%, 20%, 30% noise.
        </span>
      </div>
    </div>
  );
}
