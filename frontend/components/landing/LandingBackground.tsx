'use client';

import React, { useMemo } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

export function LandingBackground() {
  const shouldReduceMotion = useReducedMotion();

  // Seeded deterministic star-dot coordinates
  const stars = useMemo(() => {
    const list: { id: number; top: string; left: string; size: number; delay: number; duration: number }[] = [];
    let seed = 101;
    function rand() {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    }

    for (let i = 0; i < 40; i++) {
      list.push({
        id: i,
        top: `${(rand() * 95).toFixed(1)}%`,
        left: `${(rand() * 96 + 2).toFixed(1)}%`,
        size: rand() > 0.7 ? 2 : 1.5,
        delay: rand() * 4,
        duration: 2.5 + rand() * 3,
      });
    }
    return list;
  }, []);

  const crosshairs = [
    { top: '18%', left: '12%' },
    { top: '35%', left: '88%' },
    { top: '75%', left: '22%' },
  ];

  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 overflow-hidden pointer-events-none z-0"
    >
      {/* 1. Perspective Grid Layer */}
      <div
        className="absolute inset-0 flex items-center justify-center opacity-40 overflow-hidden"
        style={{
          perspective: '900px',
          maskImage:
            'radial-gradient(ellipse at 50% 50%, black 20%, transparent 75%)',
          WebkitMaskImage:
            'radial-gradient(ellipse at 50% 50%, black 20%, transparent 75%)',
        }}
      >
        <motion.div
          animate={
            shouldReduceMotion
              ? {}
              : {
                  backgroundPositionY: ['0px', '48px'],
                }
          }
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: 'linear',
          }}
          className="w-[200vw] h-[200vh] origin-center -translate-y-1/4"
          style={{
            transform: 'rotateX(62deg)',
            backgroundImage: `
              linear-gradient(to right, rgba(255, 255, 255, 0.07) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(255, 255, 255, 0.07) 1px, transparent 1px)
            `,
            backgroundSize: '48px 48px',
          }}
        />
      </div>

      {/* 2. Star-Dot Field with randomized twinkle */}
      {stars.map((star) => (
        <motion.div
          key={star.id}
          initial={{ opacity: 0.2 }}
          animate={
            shouldReduceMotion
              ? { opacity: 0.4 }
              : { opacity: [0.15, 0.85, 0.15] }
          }
          transition={{
            duration: star.duration,
            repeat: Infinity,
            delay: star.delay,
            ease: 'easeInOut',
          }}
          className="absolute rounded-full bg-white shadow-[0_0_4px_rgba(255,255,255,0.8)]"
          style={{
            top: star.top,
            left: star.left,
            width: `${star.size}px`,
            height: `${star.size}px`,
          }}
        />
      ))}

      {/* Crosshair Marks (+) */}
      {crosshairs.map((pos, idx) => (
        <div
          key={idx}
          className="absolute text-white/20 font-mono text-[10px] select-none"
          style={{ top: pos.top, left: pos.left }}
        >
          +
        </div>
      ))}

      {/* 3. Soft Radial Glow Behind Brain with breathing scale */}
      <motion.div
        animate={
          shouldReduceMotion
            ? { scale: 1 }
            : {
                scale: [1, 1.06, 1],
              }
        }
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute top-1/4 right-[5%] w-[580px] h-[580px] rounded-full -translate-y-1/4 pointer-events-none"
        style={{
          background:
            'radial-gradient(circle, rgba(255, 255, 255, 0.05) 0%, rgba(239, 68, 68, 0.08) 45%, rgba(5, 5, 6, 0) 70%)',
        }}
      />

      {/* 4. Vignette border gradient to #050506 */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(circle at 50% 50%, transparent 40%, #050506 100%)',
        }}
      />
    </div>
  );
}
