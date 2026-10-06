'use client';

import React, { useRef } from 'react';
import Image from 'next/image';
import { motion, useMotionValue, useSpring, useTransform, useReducedMotion } from 'framer-motion';

interface ReportCoverProps {
  experimentId: string;
  modelName: string;
  datasetName: string;
  dateStr?: string;
}

export function ReportCover({
  experimentId,
  modelName,
  datasetName,
  dateStr = 'October 2026',
}: ReportCoverProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { stiffness: 120, damping: 20 };
  const smoothX = useSpring(mouseX, springConfig);
  const smoothY = useSpring(mouseY, springConfig);

  const rotateX = useTransform(smoothY, [-0.5, 0.5], ['6deg', '-6deg']);
  const rotateY = useTransform(smoothX, [-0.5, 0.5], ['-6deg', '6deg']);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (shouldReduceMotion || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    mouseX.set(x);
    mouseY.set(y);
  };

  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ perspective: 1200 }}
      className="relative w-full max-w-lg mx-auto select-none"
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
        className="relative bg-surface rounded-2xl border border-white/20 p-8 shadow-2xl overflow-hidden flex flex-col justify-between aspect-[1/1.3] group transition-shadow hover:shadow-[0_20px_50px_rgba(239,68,68,0.15)]"
      >
        {/* Soft light sweep overlay on hover */}
        {!shouldReduceMotion && (
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/[0.04] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
        )}

        {/* Ambient red glow */}
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-accent/15 rounded-full blur-3xl pointer-events-none" />

        {/* Top Meta */}
        <div className="relative z-10 flex items-center justify-between border-b border-white/10 pb-4">
          <div className="font-mono text-xs text-accent font-semibold tracking-wider">
            MODEL AUTOPSY REPORT / {experimentId}
          </div>
          <span className="font-mono text-[11px] text-text-subtle">{dateStr}</span>
        </div>

        {/* Center Static Brain Render & Tagline */}
        <div className="relative z-10 my-auto flex flex-col items-center text-center space-y-4 py-4">
          <div className="relative w-36 h-36">
            <Image
              src="/assets/brain-isolated.png"
              alt="Model Autopsy Static Brain"
              fill
              sizes="144px"
              className="object-contain filter drop-shadow-[0_10px_25px_rgba(239,68,68,0.35)]"
              priority
            />
          </div>

          <div className="space-y-1">
            <h2 className="font-serif italic text-2xl sm:text-3xl text-white tracking-wide">
              Stress. Analyse. Understand. Prevent.
            </h2>
            <p className="font-manrope text-xs text-text-muted">
              {modelName} on {datasetName}
            </p>
          </div>
        </div>

        {/* Bottom Verification Seal */}
        <div className="relative z-10 pt-4 border-t border-white/10 flex items-center justify-between text-[11px] text-text-subtle font-mono">
          <span>Seeded Reproducible Run</span>
          <span className="text-white">v2026.1 Research Grade</span>
        </div>
      </motion.div>
    </div>
  );
}
