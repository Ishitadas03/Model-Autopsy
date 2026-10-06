'use client';

import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

interface CircularProgressRingProps {
  progress: number; // 0 to 100
  caption?: string;
  size?: number;
}

export function CircularProgressRing({
  progress,
  caption = 'Running stress tests…',
  size = 280,
}: CircularProgressRingProps) {
  const shouldReduceMotion = useReducedMotion();

  const strokeWidth = 10;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  // 36 tick marks around circle
  const tickCount = 36;
  const ticks = Array.from({ length: tickCount });

  return (
    <div className="relative flex flex-col items-center justify-center p-6 bg-surface rounded-xl border border-border shadow-2xl overflow-hidden">
      {/* Background ambient red glow */}
      <div className="absolute inset-0 bg-accent/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        {/* SVG Progress Ring */}
        <svg width={size} height={size} className="transform -rotate-90">
          <defs>
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
          </defs>

          {/* Background track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />

          {/* Active progress arc */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="url(#progressGradient)"
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            animate={{ strokeDashoffset }}
            transition={{
              duration: shouldReduceMotion ? 0 : 0.4,
              ease: [0.22, 1, 0.36, 1],
            }}
            strokeLinecap="round"
          />
        </svg>

        {/* Decorative thin tick marks */}
        <div className="absolute inset-4 pointer-events-none rounded-full">
          {ticks.map((_, i) => {
            const angle = (i * 360) / tickCount;
            return (
              <div
                key={i}
                className="absolute inset-0 flex justify-center"
                style={{ transform: `rotate(${angle}deg)` }}
              >
                <div className="w-[1.5px] h-2 bg-white/15 rounded-full" />
              </div>
            );
          })}
        </div>

        {/* Orbiting dots (disabled under reduced motion) */}
        {!shouldReduceMotion && (
          <>
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 9, repeat: Infinity, ease: 'linear' }}
              className="absolute inset-0 pointer-events-none flex items-center justify-center"
            >
              <div
                className="w-2.5 h-2.5 rounded-full bg-accent shadow-[0_0_10px_#ef4444]"
                style={{ transform: `translateY(-${radius}px)` }}
              />
            </motion.div>

            <motion.div
              animate={{ rotate: -360 }}
              transition={{ duration: 14, repeat: Infinity, ease: 'linear' }}
              className="absolute inset-0 pointer-events-none flex items-center justify-center"
            >
              <div
                className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_8px_#ffffff]"
                style={{ transform: `translateY(${radius - 8}px)` }}
              />
            </motion.div>
          </>
        )}

        {/* Centered Percentage and Caption */}
        <div className="absolute flex flex-col items-center justify-center text-center select-none px-4">
          <span className="font-manrope font-bold text-5xl sm:text-[56px] text-white tracking-tight tabular-nums">
            {Math.round(progress)}%
          </span>
          <span className="text-xs font-cabin text-text-subtle uppercase tracking-wider mt-1">
            {caption}
          </span>
        </div>
      </div>
    </div>
  );
}
