'use client';

import React, { useMemo } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

export function GlobalAnimatedBackground() {
  const shouldReduceMotion = useReducedMotion();

  // Deterministically generate floating ambient particles
  const particles = useMemo(() => {
    const list: {
      id: number;
      top: string;
      left: string;
      size: number;
      duration: number;
      delay: number;
      driftX: number;
      driftY: number;
      color: string;
    }[] = [];

    let seed = 42;
    function rand() {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    }

    const colors = [
      'rgba(56, 189, 248, 0.7)',  // sky-400
      'rgba(99, 102, 241, 0.6)',  // indigo-500
      'rgba(147, 197, 253, 0.5)', // blue-300
      'rgba(255, 255, 255, 0.6)', // white
      'rgba(52, 211, 153, 0.5)',  // emerald-400
    ];

    for (let i = 0; i < 65; i++) {
      list.push({
        id: i,
        top: `${(rand() * 98).toFixed(1)}%`,
        left: `${(rand() * 98 + 1).toFixed(1)}%`,
        size: rand() > 0.8 ? 2.5 : rand() > 0.4 ? 1.8 : 1.2,
        duration: 4 + rand() * 5,
        delay: rand() * 4,
        driftX: (rand() - 0.5) * 40,
        driftY: -20 - rand() * 40,
        color: colors[Math.floor(rand() * colors.length)],
      });
    }
    return list;
  }, []);

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none z-0 overflow-hidden"
    >
      {/* 1. Deep Base Vignette & Tone */}
      <div className="absolute inset-0 bg-[#050506]" />

      {/* 2. Global Cybernetic Scan Grid with subtle gradient fading */}
      <div
        className="absolute inset-0 opacity-[0.035]"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.8) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.8) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* 3. Floating Volumetric Glowing Nebulae (Continuous Organic Drift) */}
      <motion.div
        animate={
          shouldReduceMotion
            ? { opacity: 0.25 }
            : {
                x: [0, 80, -40, 0],
                y: [0, -60, 40, 0],
                scale: [1, 1.15, 0.95, 1],
                opacity: [0.35, 0.55, 0.4, 0.35],
              }
        }
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute -top-[10%] left-[10%] w-[750px] h-[750px] rounded-full blur-[140px]"
        style={{
          background:
            'radial-gradient(circle, rgba(56, 189, 248, 0.22) 0%, rgba(37, 99, 235, 0.12) 50%, transparent 75%)',
        }}
      />

      <motion.div
        animate={
          shouldReduceMotion
            ? { opacity: 0.2 }
            : {
                x: [0, -70, 50, 0],
                y: [0, 80, -30, 0],
                scale: [1, 0.9, 1.1, 1],
                opacity: [0.3, 0.5, 0.35, 0.3],
              }
        }
        transition={{
          duration: 28,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute top-[35%] -right-[5%] w-[800px] h-[800px] rounded-full blur-[160px]"
        style={{
          background:
            'radial-gradient(circle, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.1) 50%, transparent 75%)',
        }}
      />

      <motion.div
        animate={
          shouldReduceMotion
            ? { opacity: 0.15 }
            : {
                x: [0, 60, -60, 0],
                y: [0, -50, 60, 0],
                scale: [1, 1.2, 0.95, 1],
                opacity: [0.25, 0.45, 0.3, 0.25],
              }
        }
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute top-[65%] left-[5%] w-[700px] h-[700px] rounded-full blur-[150px]"
        style={{
          background:
            'radial-gradient(circle, rgba(14, 165, 233, 0.18) 0%, rgba(79, 70, 229, 0.12) 50%, transparent 75%)',
        }}
      />

      {/* 4. Moving Laser Beam Scanline */}
      <motion.div
        animate={
          shouldReduceMotion
            ? { opacity: 0 }
            : {
                y: ['-100%', '200%'],
              }
        }
        transition={{
          duration: 14,
          repeat: Infinity,
          ease: 'linear',
        }}
        className="absolute inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-sky-400/20 to-transparent blur-[1px] opacity-70"
      />

      {/* 5. Floating Star-Dust & Data Nodes with Drifting Motion */}
      {particles.map((p) => (
        <motion.div
          key={p.id}
          initial={{ opacity: 0.2 }}
          animate={
            shouldReduceMotion
              ? { opacity: 0.4 }
              : {
                  opacity: [0.15, 0.85, 0.15],
                  x: [0, p.driftX, 0],
                  y: [0, p.driftY, 0],
                  scale: [1, 1.3, 1],
                }
          }
          transition={{
            duration: p.duration,
            repeat: Infinity,
            delay: p.delay,
            ease: 'easeInOut',
          }}
          className="absolute rounded-full"
          style={{
            top: p.top,
            left: p.left,
            width: `${p.size}px`,
            height: `${p.size}px`,
            backgroundColor: p.color,
            boxShadow: `0 0 6px ${p.color}`,
          }}
        />
      ))}
    </div>
  );
}
