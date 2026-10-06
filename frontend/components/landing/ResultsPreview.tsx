'use client';

import React, { useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform, useReducedMotion } from 'framer-motion';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ReferenceLine,
} from 'recharts';
import { Card } from '../ui/Card';
import { StatCard } from '../ui/StatCard';
import { StatusPill } from '../ui/StatusPill';
import { HERO_EXPERIMENT } from '@/lib/mocks/experiments';
import { MANDATED_BOUNDARY_CAPTION } from '@/lib/metrics';

export function ResultsPreview() {
  const cardRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  // 3D tilt-on-hover physics
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const mouseXSpring = useSpring(x, { stiffness: 120, damping: 20 });
  const mouseYSpring = useSpring(y, { stiffness: 120, damping: 20 });
  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ['4deg', '-4deg']);
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ['-4deg', '4deg']);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (shouldReduceMotion || !cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    x.set(mouseX / width - 0.5);
    y.set(mouseY / height - 0.5);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const curveData = HERO_EXPERIMENT.results?.curveData || [];

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ perspective: 1200 }}
      className="w-full max-w-5xl mx-auto"
    >
      <motion.div
        style={
          shouldReduceMotion
            ? {}
            : {
                rotateX,
                rotateY,
                transformStyle: 'preserve-3d',
              }
        }
        className="rounded-card border border-border bg-surface shadow-2xl overflow-hidden transition-shadow duration-300 hover:border-border-strong hover:shadow-[0_20px_50px_rgba(0,0,0,0.8)]"
      >
        {/* Browser Chrome Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-surface-2 border-b border-border text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-accent/60" />
            <span className="w-2.5 h-2.5 rounded-full bg-warning/60" />
            <span className="w-2.5 h-2.5 rounded-full bg-success/60" />
            <span className="ml-3 font-mono text-[11px] text-text-subtle">
              modelautopsy.internal/experiments/EXP-0241/results
            </span>
          </div>
          <StatusPill status="completed" />
        </div>

        {/* Dashboard Body Preview */}
        <div className="p-6 md:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/5">
            <div>
              <span className="text-xs font-mono text-text-subtle">EXP-0241</span>
              <h3 className="font-manrope font-bold text-xl text-white">
                Autopsy Complete: Random Forest × Credit Risk Demo
              </h3>
            </div>
            <span className="text-xs font-cabin text-text-subtle">
              Gaussian Noise Stress Test
            </span>
          </div>

          {/* 4 StatCards Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Baseline F1" value={95.8} suffix="%" decimals={1} />
            <StatCard label="Worst Case F1" value={71.2} suffix="%" decimals={1} />
            <StatCard
              label="Degradation"
              value={24.6}
              prefix="−"
              suffix=" pp"
              decimals={1}
              secondaryText="−25.7% rel"
              isDegraded={true}
            />
            <StatCard
              label="Failure Boundary"
              value={23.1}
              prefix="≈ "
              suffix="%"
              decimals={1}
              caption={MANDATED_BOUNDARY_CAPTION}
            />
          </div>

          {/* Robustness Curve Chart Preview */}
          <Card className="p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-manrope font-semibold text-sm text-white">
                  Empirical Robustness Curve
                </h4>
                <p className="text-[11px] text-text-subtle mt-0.5">
                  F1 score vs. Gaussian Noise Severity (%)
                </p>
              </div>
              <div className="flex items-center gap-4 text-xs">
                <span className="flex items-center gap-1.5 text-text-muted">
                  <span className="w-3 h-0.5 bg-white border-dashed" /> Baseline (0.958)
                </span>
                <span className="flex items-center gap-1.5 text-accent font-medium">
                  <span className="w-3 h-0.5 bg-accent" /> Stressed F1
                </span>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={curveData}
                  margin={{ top: 10, right: 20, left: -20, bottom: 0 }}
                >
                  <XAxis
                    dataKey="severity"
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                    stroke="rgba(255,255,255,0.3)"
                    tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
                  />
                  <YAxis
                    domain={[0.6, 1.0]}
                    tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                    stroke="rgba(255,255,255,0.3)"
                    tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }}
                  />
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: '#0c0c0f',
                      borderColor: 'rgba(255,255,255,0.15)',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                    formatter={(value: any) => [`${(Number(value) * 100).toFixed(1)}%`, 'F1 Score']}
                    labelFormatter={(label) => `Severity: ${(Number(label) * 100).toFixed(1)}%`}
                  />
                  <ReferenceLine
                    y={0.8}
                    stroke="rgba(255,255,255,0.4)"
                    strokeDasharray="4 4"
                    label={{
                      value: 'Threshold (0.80)',
                      fill: 'rgba(255,255,255,0.6)',
                      fontSize: 10,
                      position: 'insideBottomRight',
                    }}
                  />
                  <ReferenceLine
                    x={0.231}
                    stroke="#ef4444"
                    strokeDasharray="3 3"
                    label={{
                      value: 'Boundary ≈ 23.1%',
                      fill: '#ef4444',
                      fontSize: 10,
                      position: 'top',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="baseline"
                    stroke="#ffffff"
                    strokeDasharray="5 5"
                    strokeWidth={1.5}
                    dot={false}
                    isAnimationActive={!shouldReduceMotion}
                    animationDuration={900}
                  />
                  <Line
                    type="monotone"
                    dataKey="f1"
                    stroke="#ef4444"
                    strokeWidth={2.5}
                    dot={{ fill: '#ef4444', r: 4 }}
                    activeDot={{ r: 6, fill: '#ffffff', stroke: '#ef4444' }}
                    isAnimationActive={!shouldReduceMotion}
                    animationDuration={900}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      </motion.div>
    </div>
  );
}
