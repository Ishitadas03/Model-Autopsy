'use client';

import React, { useRef, useState, MouseEvent } from 'react';
import Link from 'next/link';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import {
  ArrowRight,
  SlidersHorizontal,
  Share2,
  BarChart3,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Maximize2,
  Activity,
  Zap,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { Reveal } from '@/components/motion/Reveal';

interface VideoPlayerCardProps {
  src: string;
  poster?: string;
  streamId: string;
  streamLabel: string;
  qualityTag?: string;
  children?: React.ReactNode;
}

function CinematicVideoCard({
  src,
  poster,
  streamId,
  streamLabel,
  qualityTag = '4K · 60FPS · HDR',
  children,
}: VideoPlayerCardProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(true);
  const [isHovered, setIsHovered] = useState(false);
  const [clickRipple, setClickRipple] = useState(false);

  // 3D Motion values for cinematic perspective tilt
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const rotateXSpring = useSpring(useTransform(mouseY, [-0.5, 0.5], [7, -7]), {
    stiffness: 220,
    damping: 24,
  });
  const rotateYSpring = useSpring(useTransform(mouseX, [-0.5, 0.5], [-7, 7]), {
    stiffness: 220,
    damping: 24,
  });

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const xPct = (e.clientX - rect.left) / rect.width - 0.5;
    const yPct = (e.clientY - rect.top) / rect.height - 0.5;
    mouseX.set(xPct);
    mouseY.set(yPct);
  };

  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
    setIsHovered(false);
  };

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
    setClickRipple(true);
    setTimeout(() => setClickRipple(false), 500);
  };

  const toggleMute = (e: MouseEvent) => {
    e.stopPropagation();
    if (!videoRef.current) return;
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleFullscreen = (e: MouseEvent) => {
    e.stopPropagation();
    if (!videoRef.current) return;
    if (videoRef.current.requestFullscreen) {
      videoRef.current.requestFullscreen();
    }
  };

  return (
    <div className="relative w-full max-w-[640px] mx-auto perspective-1000 py-6">
      {/* Dynamic Volumetric Aura Glow (pulses slowly with neon depth) */}
      <div className="absolute -inset-4 sm:-inset-6 bg-gradient-to-r from-sky-500/25 via-blue-600/30 to-indigo-600/25 rounded-[40px] blur-[70px] pointer-events-none animate-pulse-glow" />

      {/* 3D Tilting Card Container */}
      <motion.div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={handleMouseLeave}
        style={{
          rotateX: rotateXSpring,
          rotateY: rotateYSpring,
          transformStyle: 'preserve-3d',
        }}
        className="relative rounded-[28px] sm:rounded-[32px] p-2 sm:p-2.5 bg-gradient-to-b from-[#131622]/90 via-[#0a0c14]/90 to-[#06070a]/95 backdrop-blur-2xl border border-white/15 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.9),0_0_40px_rgba(56,189,248,0.12)] transition-shadow duration-500 hover:shadow-[0_30px_70px_-10px_rgba(0,0,0,0.95),0_0_60px_rgba(56,189,248,0.25)]"
      >
        {/* HUD Top Monitor Header Bar */}
        <div className="flex items-center justify-between px-3 sm:px-4 py-2 border-b border-white/10 mb-1.5 select-none">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="font-mono text-[10px] tracking-wider uppercase text-white/70 font-semibold">
              {streamId}
            </span>
            <span className="text-white/20 text-[10px]">|</span>
            <span className="font-mono text-[10px] tracking-wider uppercase text-sky-400/90 font-medium hidden sm:inline">
              {streamLabel}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 font-mono text-[9px] text-white/60 tracking-widest uppercase">
              {qualityTag}
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
          </div>
        </div>

        {/* Video Viewport Frame with HUD Reticles */}
        <div
          className="relative rounded-[20px] sm:rounded-[24px] overflow-hidden bg-black aspect-[16/10] sm:aspect-video shadow-2xl cursor-pointer group"
          onClick={togglePlay}
        >
          <video
            ref={videoRef}
            src={src}
            poster={poster}
            autoPlay
            loop
            muted
            playsInline
            className="w-full h-full object-cover select-none"
          />

          {/* Cinematic subtle glass reflection gradient */}
          <div className="absolute inset-0 bg-gradient-to-tr from-black/40 via-transparent to-white/[0.04] pointer-events-none" />

          {/* HUD Target Brackets in Corners */}
          <div className="absolute top-2.5 left-2.5 w-3 h-3 border-t-2 border-l-2 border-sky-400/60 pointer-events-none transition-all duration-300 group-hover:scale-110" />
          <div className="absolute top-2.5 right-2.5 w-3 h-3 border-t-2 border-r-2 border-sky-400/60 pointer-events-none transition-all duration-300 group-hover:scale-110" />
          <div className="absolute bottom-2.5 left-2.5 w-3 h-3 border-b-2 border-l-2 border-sky-400/60 pointer-events-none transition-all duration-300 group-hover:scale-110" />
          <div className="absolute bottom-2.5 right-2.5 w-3 h-3 border-b-2 border-r-2 border-sky-400/60 pointer-events-none transition-all duration-300 group-hover:scale-110" />

          {/* Play/Pause Ripple Splash */}
          {clickRipple && (
            <motion.div
              initial={{ scale: 0.5, opacity: 0.9 }}
              animate={{ scale: 1.2, opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="absolute inset-0 m-auto w-14 h-14 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center text-white pointer-events-none"
            >
              {isPlaying ? <Play className="w-6 h-6 fill-white" /> : <Pause className="w-6 h-6" />}
            </motion.div>
          )}

          {/* Bottom Floating Control Bar */}
          <div
            className={`absolute bottom-3 left-3 right-3 flex items-center justify-between z-10 transition-all duration-300 ${
              isHovered ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1'
            }`}
          >
            <div className="flex items-center gap-1.5 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/20 shadow-xl">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  togglePlay();
                }}
                className="p-1 rounded-full text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                title={isPlaying ? 'Pause stream' : 'Play stream'}
              >
                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              </button>

              <div className="w-[1px] h-3 bg-white/20 mx-0.5" />

              <button
                type="button"
                onClick={toggleMute}
                className="flex items-center gap-1.5 p-1 rounded-full text-white/80 hover:text-white hover:bg-white/10 transition-colors"
                title={isMuted ? 'Unmute voice & audio' : 'Mute audio'}
              >
                {isMuted ? (
                  <VolumeX className="w-3.5 h-3.5 text-white/60" />
                ) : (
                  <>
                    <Volume2 className="w-3.5 h-3.5 text-sky-400" />
                    <span className="flex items-end gap-0.5 h-2.5">
                      <span className="w-0.5 h-full bg-sky-400 rounded-full animate-pulse" />
                      <span className="w-0.5 h-2 bg-sky-400 rounded-full animate-pulse delay-75" />
                      <span className="w-0.5 h-1.5 bg-sky-400 rounded-full animate-pulse delay-150" />
                    </span>
                  </>
                )}
              </button>
            </div>

            <button
              type="button"
              onClick={handleFullscreen}
              className="p-2 rounded-full bg-black/80 backdrop-blur-md text-white/80 hover:text-white hover:bg-white/10 border border-white/20 shadow-xl transition-colors"
              title="Fullscreen"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Floating overlays (chips / widgets) */}
        {children}
      </motion.div>
    </div>
  );
}

export function FeatureSpotlight() {
  return (
    <section
      id="features"
      className="relative py-28 sm:py-36 px-6 md:px-12 xl:px-[120px] bg-bg text-text border-t border-white/8 overflow-hidden"
    >
      {/* Cinematic Deep Background Flares */}
      <div className="absolute top-1/4 -left-20 w-[600px] h-[500px] bg-[radial-gradient(ellipse_at_center,rgba(56,189,248,0.12),transparent_70%)] pointer-events-none" />
      <div className="absolute bottom-1/4 -right-20 w-[600px] h-[500px] bg-[radial-gradient(ellipse_at_center,rgba(99,102,241,0.12),transparent_70%)] pointer-events-none" />

      {/* Moving Ambient Scan Grid (super subtle HD tech backdrop) */}
      <div className="absolute inset-0 bg-grid-subtle opacity-40 pointer-events-none" />

      <div className="max-w-[1440px] mx-auto space-y-32 sm:space-y-44 relative z-10">
        
        {/* =========================================================================
            ROW 1: Text on Left, Video on Right (Push Your ML Pipeline to the Breaking Point)
           ========================================================================= */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-center">
          {/* Left Column: Text & CTA */}
          <div className="lg:col-span-6 xl:col-span-5 flex flex-col gap-6">
            <Reveal>
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 text-[11px] font-bold tracking-widest uppercase shadow-[0_0_20px_rgba(56,189,248,0.2)] w-fit backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-ping" />
                <span>FEATURE SPOTLIGHT</span>
              </div>
            </Reveal>

            <Reveal delay={0.08}>
              <h2 className="font-manrope text-3xl sm:text-4xl xl:text-[48px] font-extrabold text-white leading-[1.1] tracking-tight">
                Push Your ML Pipeline{' '}
                <span className="block mt-1 sm:mt-1.5 bg-gradient-to-r from-sky-400 via-cyan-300 to-blue-400 bg-clip-text text-transparent drop-shadow-[0_0_30px_rgba(56,189,248,0.45)]">
                  to the Breaking Point.
                </span>
              </h2>
            </Reveal>

            <Reveal delay={0.16}>
              <p className="font-inter text-base sm:text-lg text-white/70 leading-relaxed max-w-[530px]">
                Run controlled stress tests, identify failure boundaries, and generate evidence-backed reports to ensure your models are ready for the real world.
              </p>
            </Reveal>

            <Reveal delay={0.24}>
              <div className="flex flex-wrap items-center gap-4 pt-2">
                <Link
                  href="/workspace"
                  className="inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-full bg-white text-black font-manrope font-semibold text-sm shadow-[0_0_30px_rgba(255,255,255,0.2)] hover:bg-[#eaeaea] hover:shadow-[0_0_40px_rgba(255,255,255,0.35)] transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 group"
                >
                  <span>Explore the Simulator</span>
                  <ArrowRight className="w-4 h-4 text-black transition-transform duration-200 group-hover:translate-x-1" />
                </Link>

                <div className="flex items-center gap-2 text-xs font-mono text-white/50">
                  <Activity className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Real-time Perturbations</span>
                </div>
              </div>
            </Reveal>
          </div>

          {/* Right Column: Video with floating chips */}
          <div className="lg:col-span-6 xl:col-span-7 flex justify-center">
            <Reveal delay={0.2}>
              <CinematicVideoCard
                src="/videos/gemini_generated_video_6cd6e082.mp4"
                streamId="HUD // SIMULATION_CORE"
                streamLabel="STRESS_INJECTION_SUITE"
                qualityTag="1080P 60FPS"
              >
                {/* Floating Chip 1: Policy Modifiers (Top-Left) with Continuous Micro-Float */}
                <motion.div
                  animate={{ y: [0, -7, 0] }}
                  transition={{ repeat: Infinity, duration: 4.2, ease: 'easeInOut' }}
                  className="absolute -top-4 -left-3 sm:-left-6 z-20 flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-[#0a0c16]/90 backdrop-blur-2xl border border-white/20 shadow-[0_12px_32px_rgba(0,0,0,0.8),0_0_20px_rgba(56,189,248,0.2)] text-white text-xs font-semibold select-none transition-transform hover:scale-105"
                >
                  <div className="w-6 h-6 rounded-full bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400 shadow-inner">
                    <SlidersHorizontal className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex flex-col">
                    <span className="font-manrope text-xs leading-none">Policy Modifiers</span>
                    <span className="font-mono text-[9px] text-sky-400/80 leading-tight">ACTIVE · 99.4%</span>
                  </div>
                </motion.div>

                {/* Floating Chip 2: Resource Allocation (Bottom-Right) with Continuous Micro-Float */}
                <motion.div
                  animate={{ y: [0, 7, 0] }}
                  transition={{ repeat: Infinity, duration: 4.6, delay: 0.6, ease: 'easeInOut' }}
                  className="absolute -bottom-4 -right-3 sm:-right-6 z-20 flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-[#0a0c16]/90 backdrop-blur-2xl border border-white/20 shadow-[0_12px_32px_rgba(0,0,0,0.8),0_0_20px_rgba(59,130,246,0.2)] text-white text-xs font-semibold select-none transition-transform hover:scale-105"
                >
                  <div className="w-6 h-6 rounded-full bg-blue-500/20 border border-blue-500/40 flex items-center justify-center text-blue-400 shadow-inner">
                    <Share2 className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex flex-col">
                    <span className="font-manrope text-xs leading-none">Resource Allocation</span>
                    <span className="font-mono text-[9px] text-emerald-400/90 leading-tight">OPTIMIZED · 8.4m</span>
                  </div>
                </motion.div>
              </CinematicVideoCard>
            </Reveal>
          </div>
        </div>

        {/* =========================================================================
            ROW 2: Video on Left, Text on Right (Uncover the Hidden Weaknesses in Your ML Models)
           ========================================================================= */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-14 items-center">
          {/* Left Column: Video with floating Feature Importance card */}
          <div className="lg:col-span-6 xl:col-span-7 flex justify-center order-2 lg:order-1">
            <Reveal delay={0.2}>
              <CinematicVideoCard
                src="/videos/gemini_generated_video_ba9000d2.mp4"
                streamId="HUD // PIPELINE_EXPLAIN"
                streamLabel="FEATURE_DIAGNOSTICS"
                qualityTag="AUTOPSY HD"
              >
                {/* Floating Card: Feature Importance with Micro-Levitation & Shimmer Progress */}
                <motion.div
                  animate={{ y: [0, -6, 0] }}
                  transition={{ repeat: Infinity, duration: 5.2, ease: 'easeInOut' }}
                  className="absolute -bottom-6 -right-3 sm:-right-8 z-20 w-[240px] sm:w-[285px] p-4 sm:p-4.5 rounded-2xl bg-[#090b14]/92 backdrop-blur-2xl border border-white/20 shadow-[0_20px_45px_rgba(0,0,0,0.85),0_0_30px_rgba(56,189,248,0.18)] text-white select-none transition-all hover:scale-[1.02]"
                >
                  <div className="flex items-center justify-between mb-3 pb-2.5 border-b border-white/10">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="w-3.5 h-3.5 text-sky-400" />
                      <span className="text-[11px] font-extrabold tracking-wider uppercase text-white/90 font-manrope">
                        FEATURE IMPORTANCE
                      </span>
                    </div>
                    <span className="font-mono text-[9px] text-emerald-400 px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                      LIVE
                    </span>
                  </div>

                  <div className="space-y-2.5 text-xs font-medium">
                    {/* Bar 1: Historical Density */}
                    <div className="flex items-center justify-between gap-2.5">
                      <span className="text-white/70 truncate max-w-[95px] text-[11px]">
                        Historical Den...
                      </span>
                      <div className="flex items-center gap-2 flex-1">
                        <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-blue-600 via-sky-400 to-blue-600 rounded-full w-[82%] animate-shimmer" />
                        </div>
                        <span className="font-mono text-[10px] text-white/50 w-6 text-right">82%</span>
                      </div>
                    </div>

                    {/* Bar 2: Time of Day */}
                    <div className="flex items-center justify-between gap-2.5">
                      <span className="text-white/70 truncate max-w-[95px] text-[11px]">
                        Time of Day
                      </span>
                      <div className="flex items-center gap-2 flex-1">
                        <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-sky-500 via-cyan-300 to-sky-500 rounded-full w-[60%] animate-shimmer" />
                        </div>
                        <span className="font-mono text-[10px] text-white/50 w-6 text-right">60%</span>
                      </div>
                    </div>

                    {/* Bar 3: Event Proximity */}
                    <div className="flex items-center justify-between gap-2.5">
                      <span className="text-white/70 truncate max-w-[95px] text-[11px]">
                        Event Proximity
                      </span>
                      <div className="flex items-center gap-2 flex-1">
                        <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-indigo-500 via-purple-400 to-indigo-500 rounded-full w-[38%] animate-shimmer" />
                        </div>
                        <span className="font-mono text-[10px] text-white/50 w-6 text-right">38%</span>
                      </div>
                    </div>

                    {/* Bar 4: Weather Index with interactive indicator */}
                    <div className="flex items-center justify-between gap-2.5">
                      <span className="text-white/70 truncate max-w-[95px] text-[11px]">
                        Weather Index
                      </span>
                      <div className="flex items-center gap-2 flex-1 justify-end">
                        <div className="w-12 h-2 rounded-full bg-white/10 overflow-hidden">
                          <div className="h-full bg-sky-400 rounded-full w-[45%]" />
                        </div>
                        <div className="w-7 h-4 rounded-full bg-sky-500/20 border border-sky-500/40 p-0.5 flex items-center justify-end">
                          <div className="w-2.5 h-2.5 rounded-full bg-sky-400 shadow-[0_0_8px_#38bdf8]" />
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </CinematicVideoCard>
            </Reveal>
          </div>

          {/* Right Column: Text & CTA */}
          <div className="lg:col-span-6 xl:col-span-5 flex flex-col gap-6 order-1 lg:order-2">
            <Reveal>
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-400/30 text-blue-400 text-[11px] font-bold tracking-widest uppercase shadow-[0_0_20px_rgba(59,130,246,0.2)] w-fit backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-ping" />
                <span>EXPLAINABLE AI</span>
              </div>
            </Reveal>

            <Reveal delay={0.08}>
              <h2 className="font-manrope text-3xl sm:text-4xl xl:text-[48px] font-extrabold text-white leading-[1.1] tracking-tight">
                Uncover the Hidden Weaknesses{' '}
                <span className="block mt-1 sm:mt-1.5 bg-gradient-to-r from-sky-400 via-cyan-300 to-blue-400 bg-clip-text text-transparent drop-shadow-[0_0_30px_rgba(56,189,248,0.45)]">
                  in Your ML Models.
                </span>
              </h2>
            </Reveal>

            <Reveal delay={0.16}>
              <p className="font-inter text-base sm:text-lg text-white/70 leading-relaxed max-w-[530px]">
                From clean baselines to extreme feature corruption, automate your robustness testing with Model Autopsy.
              </p>
            </Reveal>

            <Reveal delay={0.24}>
              <div className="flex flex-wrap items-center gap-4 pt-2">
                <Link
                  href="/workspace"
                  className="inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-full bg-white text-black font-manrope font-semibold text-sm shadow-[0_0_30px_rgba(255,255,255,0.2)] hover:bg-[#eaeaea] hover:shadow-[0_0_40px_rgba(255,255,255,0.35)] transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 group"
                >
                  <span>See Model Transparency</span>
                  <ArrowRight className="w-4 h-4 text-black transition-transform duration-200 group-hover:translate-x-1" />
                </Link>

                <div className="flex items-center gap-2 text-xs font-mono text-white/50">
                  <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
                  <span>SHAP & Permutation Analysis</span>
                </div>
              </div>
            </Reveal>
          </div>
        </div>

      </div>
    </section>
  );
}
