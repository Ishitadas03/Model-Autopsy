'use client';

import React, { useRef, useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform, useReducedMotion } from 'framer-motion';
import { Activity, ShieldAlert, Cpu, Sparkles, AlertCircle, Crosshair } from 'lucide-react';
import Image from 'next/image';

interface Hotspot {
  id: string;
  x: string;
  y: string;
  label: string;
  detail: string;
  metric: string;
}

const HOTSPOTS: Hotspot[] = [
  {
    id: 'frontal',
    x: '34%',
    y: '38%',
    label: 'Frontal Cortex',
    detail: 'Semantic drift under token perturbation',
    metric: 'Loss +4.8x',
  },
  {
    id: 'parietal',
    x: '52%',
    y: '33%',
    label: 'Superior Parietal',
    detail: 'Feature representation collapse',
    metric: 'Drift 0.42',
  },
  {
    id: 'temporal',
    x: '42%',
    y: '50%',
    label: 'Temporal Sulcus',
    detail: 'Adversarial frequency boundary',
    metric: 'Fail @ 23.1%',
  },
];

export function RotatingBrain() {
  const shouldReduceMotion = useReducedMotion();
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeHotspot, setActiveHotspot] = useState<Hotspot | null>(null);

  // Mouse 3D tilt tracking using Framer Motion springs
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { stiffness: 100, damping: 22 };
  const smoothMouseX = useSpring(mouseX, springConfig);
  const smoothMouseY = useSpring(mouseY, springConfig);

  const rotateX = useTransform(smoothMouseY, [-0.5, 0.5], ['14deg', '-14deg']);
  const rotateY = useTransform(smoothMouseX, [-0.5, 0.5], ['-16deg', '16deg']);

  // Parallax offsets for floating brain relative to hands
  const brainParallaxX = useTransform(smoothMouseX, [-0.5, 0.5], ['-10px', '10px']);
  const brainParallaxY = useTransform(smoothMouseY, [-0.5, 0.5], ['-10px', '10px']);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (shouldReduceMotion || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5; // -0.5 to 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    mouseX.set(x);
    mouseY.set(y);
  };

  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
    setActiveHotspot(null);
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ perspective: 1400 }}
      className="relative w-full max-w-[480px] lg:max-w-[540px] xl:max-w-[600px] aspect-[708/1020] flex items-center justify-center select-none"
    >
      {/* 1. Deep Core Ambient Backlight */}
      <div
        className="absolute inset-8 rounded-full pointer-events-none"
        style={{
          background:
            'radial-gradient(circle at 45% 46%, rgba(239, 68, 68, 0.24) 0%, rgba(255, 255, 255, 0.05) 35%, transparent 68%)',
          filter: 'blur(45px)',
        }}
      />

      {/* 2. Tactical Telemetry HUD Overlay */}
      <div className="absolute inset-0 pointer-events-none z-30 flex flex-col justify-between p-3 sm:p-5 font-mono text-[11px]">
        {/* Top Header Row */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-[8px] bg-black/75 border border-white/10 backdrop-blur-md shadow-xl">
            <span className="w-2 h-2 rounded-full bg-accent animate-ping" />
            <span className="text-white/80">STATUS:</span>
            <span className="text-accent font-semibold uppercase tracking-wider text-[10px] sm:text-[11px]">
              Stress Scanning...
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-[8px] bg-black/75 border border-accent/30 backdrop-blur-md shadow-xl">
            <Activity className="w-3.5 h-3.5 text-accent" />
            <span className="text-white/80 hidden sm:inline">FAIL BOUNDARY:</span>
            <span className="text-accent font-bold text-sm tabular-nums">
              ≈ 23.1%
            </span>
          </div>
        </div>

        {/* Hotspot detail popup when hovering a cortical node */}
        {activeHotspot && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="self-center px-4 py-2 rounded-[8px] bg-black/85 border border-accent/60 backdrop-blur-xl shadow-2xl text-center pointer-events-auto"
          >
            <div className="flex items-center justify-center gap-2 text-accent font-bold text-xs uppercase tracking-wider">
              <Crosshair className="w-3.5 h-3.5" />
              <span>{activeHotspot.label}</span>
              <span className="text-white/40">|</span>
              <span className="text-white tabular-nums">{activeHotspot.metric}</span>
            </div>
            <p className="text-white/70 text-[10px] mt-0.5">{activeHotspot.detail}</p>
          </motion.div>
        )}

        {/* Bottom Telemetry Row */}
        <div className="flex items-end justify-between">
          <div className="flex flex-col gap-1 text-left px-3 py-2 rounded-[8px] bg-black/75 border border-white/10 backdrop-blur-md shadow-xl">
            <div className="flex items-center gap-1.5 text-white/50 text-[10px]">
              <Cpu className="w-3 h-3 text-cyan-400" />
              <span>EMPIRICAL CORTICAL SURFACE</span>
            </div>
            <span className="text-white text-xs font-semibold">
              Frontal Lobe Vulnerability Zone
            </span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-[8px] bg-accent/20 border border-accent/40 backdrop-blur-md shadow-xl">
            <AlertCircle className="w-3.5 h-3.5 text-accent animate-pulse" />
            <span className="text-accent font-semibold tracking-wider uppercase text-[10px]">
              143 Failures Detected
            </span>
          </div>
        </div>
      </div>

      {/* 3. 3D Perspective Tilt Stage */}
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
        className="relative w-full h-full flex items-center justify-center"
      >
        {/* Layer 1: Background Hands (Hovering & Cupping) */}
        <motion.div
          animate={
            shouldReduceMotion
              ? {}
              : {
                  y: [3, -3, 3],
                  rotateZ: [0.3, -0.3, 0.3],
                }
          }
          transition={{
            duration: 6.0,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          style={{ transform: 'translateZ(0px)' }}
          className="absolute inset-0 w-full h-full pointer-events-none"
        >
          <Image
            src="/assets/hands-layer-cropped.png"
            alt="Hovering hands"
            fill
            sizes="(max-width: 768px) 100vw, 600px"
            priority
            className="object-contain filter contrast-125 brightness-105"
          />
        </motion.div>

        {/* Layer 2: Floating Animated Human Brain (Mid-air between hands) */}
        <motion.div
          animate={
            shouldReduceMotion
              ? {}
              : {
                  y: [-11, 11, -11],
                  rotateZ: [-2, 2, -2],
                  scale: [0.99, 1.025, 0.99],
                }
          }
          transition={{
            duration: 3.8,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          style={
            shouldReduceMotion
              ? { transformOrigin: '44.9% 45.6%' }
              : {
                  transformOrigin: '44.9% 45.6%',
                  x: brainParallaxX,
                  y: brainParallaxY,
                  transform: 'translateZ(45px)',
                }
          }
          className="absolute inset-0 w-full h-full pointer-events-none"
        >
          <Image
            src="/assets/brain-layer-cropped.png"
            alt="Floating animated brain"
            fill
            sizes="(max-width: 768px) 100vw, 600px"
            priority
            className="object-contain filter contrast-125 brightness-110 drop-shadow-[0_15px_30px_rgba(0,0,0,0.85)]"
          />

          {/* Autopsy Laser Scanning Sweep Beam across Brain Surface */}
          {!shouldReduceMotion && (
            <motion.div
              animate={{
                top: ['25%', '66%', '25%'],
                opacity: [0.2, 0.85, 0.2],
              }}
              transition={{
                duration: 4.4,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className="absolute left-[10%] right-[18%] h-[2px] bg-gradient-to-r from-transparent via-accent to-transparent pointer-events-none shadow-[0_0_18px_#ef4444]"
            />
          )}

          {/* Interactive Cortical Hotspots on the Floating Brain */}
          <div className="absolute inset-0 pointer-events-auto">
            {HOTSPOTS.map((spot) => (
              <button
                key={spot.id}
                type="button"
                aria-label={`Inspect ${spot.label}`}
                onMouseEnter={() => setActiveHotspot(spot)}
                onMouseLeave={() => setActiveHotspot(null)}
                onClick={() => setActiveHotspot(spot)}
                style={{ left: spot.x, top: spot.y }}
                className="absolute -translate-x-1/2 -translate-y-1/2 p-2 group cursor-pointer focus:outline-none"
              >
                <span className="relative flex h-3 w-3 items-center justify-center">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-accent shadow-[0_0_8px_#ef4444] group-hover:scale-150 transition-transform duration-200" />
                </span>
              </button>
            ))}
          </div>
        </motion.div>

        {/* Layer 3: Foreground Fingertips for True 3D Depth Clipping */}
        <motion.div
          animate={
            shouldReduceMotion
              ? {}
              : {
                  y: [3, -3, 3],
                  rotateZ: [0.3, -0.3, 0.3],
                }
          }
          transition={{
            duration: 6.0,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          style={{ transform: 'translateZ(65px)' }}
          className="absolute inset-0 w-full h-full pointer-events-none"
        >
          <Image
            src="/assets/fingertips-layer-cropped.png"
            alt="Foreground fingertips"
            fill
            sizes="(max-width: 768px) 100vw, 600px"
            priority
            className="object-contain filter contrast-125 brightness-105"
          />
        </motion.div>
      </motion.div>
    </div>
  );
}
