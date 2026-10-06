'use client';

import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Table as TableIcon, Download, SlidersHorizontal, Activity } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';

interface CurvePoint {
  severity: number;
  f1?: number;
  accuracy?: number;
  mae?: number;
  rmse?: number;
  baseline: number;
  threshold: number;
  svmF1?: number; // multi-model overlay
}

interface RobustnessCurveProps {
  curveData: CurvePoint[];
  metricKey?: 'f1' | 'accuracy' | 'mae' | 'rmse';
  failureThreshold?: number;
  observedBoundary?: number | null;
  metricLabel?: string;
  isLowerBetter?: boolean;
}

export function RobustnessCurve({
  curveData,
  metricKey = 'f1',
  failureThreshold = 0.8,
  observedBoundary = 0.231,
  metricLabel = 'F1 Score',
  isLowerBetter = false,
}: RobustnessCurveProps) {
  const [showTable, setShowTable] = useState(false);
  const [showOverlay, setShowOverlay] = useState(false);
  const [activeMetric, setActiveMetric] = useState<'f1' | 'accuracy'>('f1');

  // Multi-model overlay synthetic comparison
  const displayData = curveData.map((d) => ({
    ...d,
    severityPercent: `${Math.round(d.severity * 100)}%`,
    svmF1: d.f1 !== undefined ? parseFloat((d.f1 * 0.94).toFixed(3)) : undefined,
  }));

  const handleExportCsv = () => {
    const headers = ['Severity (%)', metricLabel, 'Baseline', 'Threshold'];
    const rows = displayData.map((d) => [
      d.severityPercent,
      (d as any)[activeMetric] ?? 'N/A',
      d.baseline,
      d.threshold,
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'robustness-curve.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-white/5">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-accent" />
            <h3 className="font-manrope font-semibold text-sm text-white">
              Robustness Degradation Curve
            </h3>
          </div>
          <p className="text-xs text-text-subtle mt-0.5">
            Model performance under escalating noise perturbation severities.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Multi-model overlay toggle */}
          <Button
            variant={showOverlay ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setShowOverlay(!showOverlay)}
            className="text-xs gap-1"
          >
            <span>Compare: SVM</span>
          </Button>

          {/* Accessible Table view toggle */}
          <Button
            variant={showTable ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setShowTable(!showTable)}
            className="text-xs gap-1.5"
            aria-label="Toggle accessible data table view"
          >
            <TableIcon className="w-3.5 h-3.5" />
            <span>{showTable ? 'View Chart' : 'View as table'}</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={handleExportCsv}
            className="text-xs gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </Button>
        </div>
      </div>

      {showTable ? (
        /* Accessible Table Alternative */
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Noise Severity</TableHead>
                <TableHead>{metricLabel}</TableHead>
                <TableHead>Baseline</TableHead>
                <TableHead>Failure Threshold</TableHead>
                {showOverlay && <TableHead>SVM Comparison</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {displayData.map((row, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-mono text-white font-medium">
                    {row.severityPercent}
                  </TableCell>
                  <TableCell className="font-mono text-white font-semibold">
                    {row[activeMetric] ?? '—'}
                  </TableCell>
                  <TableCell className="font-mono text-text-subtle">
                    {row.baseline}
                  </TableCell>
                  <TableCell className="font-mono text-accent">
                    {row.threshold}
                  </TableCell>
                  {showOverlay && (
                    <TableCell className="font-mono text-cyan-400">
                      {row.svmF1 ?? '—'}
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        /* Recharts Visualization */
        <div className="space-y-4">
          {/* Chart Legend with accessible markers & dash descriptions */}
          <div className="flex items-center gap-6 text-xs font-mono flex-wrap pt-1">
            <div className="flex items-center gap-2">
              <span className="w-4 h-0.5 bg-white border-t border-dashed" />
              <span className="text-white">Clean Baseline ({curveData[0]?.baseline})</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-accent inline-block" />
              <span className="text-accent font-medium">Stressed Model (Random Forest)</span>
            </div>
            {showOverlay && (
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 bg-cyan-400 rotate-45 inline-block" />
                <span className="text-cyan-400">SVM Classifier</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <span className="w-4 h-0.5 bg-accent border-t-2 border-dotted" />
              <span className="text-text-subtle">Failure Threshold ({failureThreshold})</span>
            </div>
            {observedBoundary && (
              <div className="flex items-center gap-2">
                <span className="w-0.5 h-3 bg-yellow-400 inline-block" />
                <span className="text-yellow-400 font-semibold">
                  Boundary ≈ {(observedBoundary * 100).toFixed(1)}%
                </span>
              </div>
            )}
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={displayData} margin={{ top: 15, right: 30, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis
                  dataKey="severityPercent"
                  stroke="rgba(255,255,255,0.4)"
                  fontSize={11}
                  fontFamily="monospace"
                />
                <YAxis
                  domain={isLowerBetter ? [0, 'auto'] : [0.65, 1.0]}
                  stroke="rgba(255,255,255,0.4)"
                  fontSize={11}
                  fontFamily="monospace"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0c0c0f',
                    borderColor: 'rgba(255,255,255,0.2)',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                  }}
                />

                {/* Horizontal Baseline line */}
                <ReferenceLine
                  y={curveData[0]?.baseline}
                  stroke="#ffffff"
                  strokeDasharray="4 4"
                  strokeOpacity={0.7}
                  label={{
                    value: `Baseline (${curveData[0]?.baseline})`,
                    fill: '#ffffff',
                    fontSize: 10,
                    position: 'insideTopLeft',
                  }}
                />

                {/* Horizontal Failure Threshold line */}
                <ReferenceLine
                  y={failureThreshold}
                  stroke="#ef4444"
                  strokeDasharray="3 3"
                  strokeOpacity={0.8}
                  label={{
                    value: `Failure Threshold (${failureThreshold})`,
                    fill: '#ef4444',
                    fontSize: 10,
                    position: 'insideBottomRight',
                  }}
                />

                {/* Vertical Observed Boundary line */}
                {observedBoundary && (
                  <ReferenceLine
                    x={`${(observedBoundary * 100).toFixed(1)}%`}
                    stroke="#f59e0b"
                    strokeDasharray="3 3"
                    strokeWidth={1.5}
                    label={{
                      value: `Boundary: ${(observedBoundary * 100).toFixed(1)}%`,
                      fill: '#f59e0b',
                      fontSize: 10,
                      position: 'top',
                    }}
                  />
                )}

                {/* Stressed Line (Solid Red with Circle dots) */}
                <Line
                  type="monotone"
                  dataKey={activeMetric}
                  name="Random Forest"
                  stroke="#ef4444"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#ef4444', strokeWidth: 1, stroke: '#ffffff' }}
                  activeDot={{ r: 6 }}
                  isAnimationActive
                  animationDuration={900}
                />

                {/* Multi-model comparison line (Cyan with Diamond dots) */}
                {showOverlay && (
                  <Line
                    type="monotone"
                    dataKey="svmF1"
                    name="SVM Classifier"
                    stroke="#22d3ee"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={{ r: 4, fill: '#22d3ee' }}
                    activeDot={{ r: 6 }}
                    isAnimationActive
                    animationDuration={900}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
