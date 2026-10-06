import React from 'react';
import { Card } from './Card';
import { CountUp } from '../motion/CountUp';
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';

export interface StatCardProps {
  label: string;
  value: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  secondaryText?: string;
  isDegraded?: boolean;
  isImproved?: boolean;
  caption?: string;
  className?: string;
}

export function StatCard({
  label,
  value,
  decimals = 1,
  prefix = '',
  suffix = '',
  secondaryText,
  isDegraded,
  isImproved,
  caption,
  className = '',
}: StatCardProps) {
  return (
    <Card className={`p-5 flex flex-col justify-between ${className}`}>
      <div className="flex items-center justify-between text-xs font-cabin uppercase tracking-wider text-text-subtle mb-3">
        <span>{label}</span>
        {isDegraded && (
          <span
            className="flex items-center gap-1 text-accent font-medium text-xs normal-case"
            aria-label="Degraded performance"
          >
            <TrendingDown className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Degraded</span>
          </span>
        )}
        {isImproved && (
          <span
            className="flex items-center gap-1 text-success font-medium text-xs normal-case"
            aria-label="Improved performance"
          >
            <TrendingUp className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Improved</span>
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span className="font-manrope font-bold text-3xl md:text-4xl text-white">
          <CountUp
            value={value}
            decimals={decimals}
            prefix={prefix}
            suffix={suffix}
          />
        </span>
        {secondaryText && (
          <span className="text-xs text-text-muted font-medium tabular-nums">
            {secondaryText}
          </span>
        )}
      </div>

      {caption && (
        <p className="mt-2 text-[11px] leading-tight text-text-subtle italic border-t border-white/5 pt-2">
          {caption}
        </p>
      )}
    </Card>
  );
}
