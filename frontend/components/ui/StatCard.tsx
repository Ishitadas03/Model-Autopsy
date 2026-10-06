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
  const topRimColor = isDegraded
    ? 'border-t-rose-500/70'
    : isImproved
    ? 'border-t-emerald-400/70'
    : 'border-t-sky-400/50';

  return (
    <Card
      hoverEffect
      className={`p-5 sm:p-6 flex flex-col justify-between border-t-2 ${topRimColor} relative group overflow-hidden ${className}`}
    >
      {/* Top subtle inner glow on hover */}
      <div className="absolute top-0 inset-x-0 h-10 bg-gradient-to-b from-white/[0.03] to-transparent pointer-events-none" />

      <div className="flex items-center justify-between text-xs font-mono uppercase tracking-wider text-white/50 mb-3 relative z-10">
        <span className="font-semibold text-white/70">{label}</span>
        {isDegraded && (
          <span
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-500/30 text-rose-400 font-mono text-[10px] font-semibold tracking-normal shadow-[0_0_8px_rgba(244,63,94,0.2)]"
            aria-label="Degraded performance"
          >
            <TrendingDown className="w-3 h-3" aria-hidden="true" />
            <span>Degraded</span>
          </span>
        )}
        {isImproved && (
          <span
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono text-[10px] font-semibold tracking-normal shadow-[0_0_8px_rgba(52,211,153,0.2)]"
            aria-label="Improved performance"
          >
            <TrendingUp className="w-3 h-3" aria-hidden="true" />
            <span>Improved</span>
          </span>
        )}
      </div>

      <div className="flex items-baseline gap-2.5 relative z-10">
        <span className="font-manrope font-extrabold text-3xl sm:text-4xl text-white tracking-tight drop-shadow-sm">
          <CountUp
            value={value}
            decimals={decimals}
            prefix={prefix}
            suffix={suffix}
          />
        </span>
        {secondaryText && (
          <span className="text-xs text-rose-400/90 font-mono font-medium tabular-nums bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
            {secondaryText}
          </span>
        )}
      </div>

      {caption && (
        <p className="mt-3 text-[11px] leading-relaxed text-white/40 italic border-t border-white/8 pt-2.5 relative z-10">
          {caption}
        </p>
      )}
    </Card>
  );
}
