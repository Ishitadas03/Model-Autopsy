'use client';

import React from 'react';
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
import { Activity, Clock, Database, Gauge, Zap } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

interface LiveTelemetryProps {
  currentStage: string;
  progressPercent: number;
  elapsedSeconds: number;
  metric?: string;
  baselineScore?: number;
}

export function LiveTelemetry({
  currentStage,
  progressPercent,
  elapsedSeconds,
  metric = 'F1',
  baselineScore = 0.958,
}: LiveTelemetryProps) {
  // Format elapsed time as mm:ss
  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;
  const formattedTime = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  // Telemetry curve points based on progress
  const chartData = [
    { progress: 0, score: baselineScore, baseline: baselineScore },
    { progress: 20, score: 0.924, baseline: baselineScore },
    { progress: 40, score: 0.885, baseline: baselineScore },
    { progress: 60, score: 0.824, baseline: baselineScore },
    { progress: 80, score: 0.765, baseline: baselineScore },
    { progress: 100, score: 0.712, baseline: baselineScore },
  ].filter((d) => d.progress <= Math.max(20, progressPercent));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Live Performance Chart (2 cols) */}
      <div className="lg:col-span-2 p-5 rounded-xl bg-surface border border-border shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-accent" />
            <h4 className="font-manrope font-semibold text-xs text-white uppercase tracking-wider">
              Live Performance ({metric.toUpperCase()} vs Test Progress)
            </h4>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-0.5 bg-white border-t border-dashed" />
              <span className="text-text-subtle">Baseline ({baselineScore})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-1.5 rounded-full bg-accent" />
              <span className="text-accent">Under Stress</span>
            </div>
          </div>
        </div>

        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis
                dataKey="progress"
                unit="%"
                stroke="rgba(255,255,255,0.3)"
                fontSize={11}
                fontFamily="monospace"
              />
              <YAxis
                domain={[0.65, 1.0]}
                stroke="rgba(255,255,255,0.3)"
                fontSize={11}
                fontFamily="monospace"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0c0c0f',
                  borderColor: 'rgba(255,255,255,0.15)',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                }}
              />
              <ReferenceLine
                y={baselineScore}
                stroke="#ffffff"
                strokeDasharray="4 4"
                strokeOpacity={0.6}
              />
              <Line
                type="monotone"
                dataKey="score"
                name={metric.toUpperCase()}
                stroke="#ef4444"
                strokeWidth={2.5}
                dot={{ r: 4, fill: '#ef4444' }}
                activeDot={{ r: 6 }}
                isAnimationActive
                animationDuration={900}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Current Test Telemetry (1 col) */}
      <div className="p-5 rounded-xl bg-surface border border-border shadow-xl flex flex-col justify-between space-y-4">
        <div>
          <div className="flex items-center justify-between pb-3 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Gauge className="w-4 h-4 text-accent" />
              <h4 className="font-manrope font-semibold text-xs text-white uppercase tracking-wider">
                Current Test
              </h4>
            </div>
            <span className="w-2 h-2 rounded-full bg-accent animate-ping" />
          </div>

          <div className="mt-4 space-y-3">
            <div>
              <span className="text-[10px] font-cabin uppercase text-text-subtle">
                Perturbation Stage
              </span>
              <p className="font-manrope font-bold text-sm text-accent mt-0.5">
                {currentStage}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="p-3 rounded-lg bg-surface-2 border border-border">
                <div className="flex items-center gap-1.5 text-text-subtle text-[10px] font-cabin uppercase">
                  <Database className="w-3 h-3" />
                  <span>Samples</span>
                </div>
                <div className="text-base font-bold font-mono text-white mt-1">
                  1,000
                </div>
              </div>

              <div className="p-3 rounded-lg bg-surface-2 border border-border">
                <div className="flex items-center gap-1.5 text-text-subtle text-[10px] font-cabin uppercase">
                  <Zap className="w-3 h-3" />
                  <span>Batch Progress</span>
                </div>
                <div className="text-base font-bold font-mono text-white mt-1">
                  {Math.round(progressPercent)}%
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-3 border-t border-white/5 flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-text-subtle">
            <Clock className="w-3.5 h-3.5 text-text-subtle" />
            <span>Elapsed:</span>
          </div>
          <span className="font-mono text-white font-bold text-sm tabular-nums">
            {formattedTime}
          </span>
        </div>
      </div>
    </div>
  );
}
