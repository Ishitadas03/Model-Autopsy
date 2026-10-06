'use client';

import React from 'react';
import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowRight,
  Database,
  Cpu,
  Gauge,
  Zap,
  CheckCircle2,
  FileCheck2,
  Activity,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react';
import { LandingNavbar } from '@/components/landing/LandingNavbar';
import { LandingBackground } from '@/components/landing/LandingBackground';
import { RotatingBrain } from '@/components/landing/RotatingBrain';
import { ResultsPreview } from '@/components/landing/ResultsPreview';
import { FeatureSpotlight } from '@/components/landing/FeatureSpotlight';
import { GlobalAnimatedBackground } from '@/components/landing/GlobalAnimatedBackground';
import { CountUp } from '@/components/motion/CountUp';
import { Reveal } from '@/components/motion/Reveal';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { Logo } from '@/components/ui/Logo';

export default function LandingPage() {
  const shouldReduceMotion = useReducedMotion();

  const words = ['Find', 'out', 'why', 'AI', 'Models'];

  return (
    <div className="relative min-h-screen bg-bg text-text selection:bg-accent/30 selection:text-white overflow-x-hidden">
      {/* Cinematic Full-Page Continuous Animated Background */}
      <GlobalAnimatedBackground />

      {/* Dynamic Landing Navbar */}
      <LandingNavbar />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center pt-24 pb-16 px-6 md:px-12 xl:px-[120px] overflow-hidden z-10">
        {/* Background Atmosphere Layers */}
        <LandingBackground />

        <div className="relative z-10 w-full max-w-[1440px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column: Hero Content (~45% on desktop) */}
          <div className="lg:col-span-6 xl:col-span-5 flex flex-col gap-6 max-w-[580px]">
            {/* Eyebrow */}
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              className="flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-accent animate-pulse shadow-[0_0_8px_#ef4444]" />
              <span className="font-cabin font-medium text-xs tracking-[0.2em] uppercase text-white/60">
                AI Model Reliability Lab
              </span>
            </motion.div>

            {/* Headline with Glitch on "Fail." */}
            <h1 className="font-serif text-white text-[48px] sm:text-[64px] xl:text-[84px] leading-[1.04] tracking-[-0.01em]">
              <span className="inline">
                {words.map((w, idx) => (
                  <motion.span
                    key={idx}
                    initial={
                      shouldReduceMotion
                        ? { opacity: 1 }
                        : { opacity: 0, y: 40, filter: 'blur(8px)' }
                    }
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    transition={{
                      delay: 0.08 * idx,
                      duration: 0.6,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                    className="inline-block mr-3"
                  >
                    {w}
                  </motion.span>
                ))}
              </span>
              <br />
              <motion.span
                initial={
                  shouldReduceMotion
                    ? { opacity: 1 }
                    : { opacity: 0, y: 40, filter: 'blur(8px)' }
                }
                animate={
                  shouldReduceMotion
                    ? { opacity: 1, y: 0, filter: 'blur(0px)' }
                    : {
                        opacity: [0, 1, 0.8, 1],
                        x: [0, -2, 2, 0],
                        y: 0,
                        filter: 'blur(0px)',
                      }
                }
                transition={{
                  delay: 0.45,
                  duration: 0.65,
                  ease: [0.22, 1, 0.36, 1],
                }}
                className="inline-block text-accent italic font-serif transition-shadow duration-700 hover:drop-shadow-[0_0_20px_rgba(239,68,68,0.7)]"
                style={{
                  textShadow: '0 0 24px rgba(239, 68, 68, 0.4)',
                }}
              >
                Fail.
              </motion.span>
            </h1>

            {/* Subtext */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="font-inter text-base md:text-lg text-white/70 max-w-[520px] leading-relaxed"
            >
              Systematically stress-test machine learning models, measure their robustness, and discover the conditions where their performance breaks down.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.65, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="flex flex-wrap items-center gap-3 pt-2"
            >
              <Link
                href="/workspace"
                className="inline-flex items-center justify-center gap-2.5 h-12 px-6 rounded-[10px] bg-white text-black font-cabin font-medium text-base shadow-lg transition-all duration-200 hover:bg-[#e8e8e8] hover:scale-[1.02] active:scale-[0.98] group"
              >
                <span>Run an Autopsy</span>
                <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
              </Link>

              <a
                href="#features"
                className="inline-flex items-center justify-center gap-2 h-12 px-5 rounded-[10px] border border-white/20 text-white font-cabin font-medium text-base transition-all duration-200 hover:border-white/50 hover:bg-white/5 active:scale-[0.98]"
              >
                <span>▷ Watch Video Teaser</span>
              </a>
            </motion.div>

            {/* Honest Stats Row */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-6 border-t border-white/8 mt-2"
            >
              <div>
                <p className="font-manrope font-bold text-2xl md:text-3xl text-white">
                  <CountUp value={5} decimals={0} />
                </p>
                <p className="font-inter text-xs text-white/50 mt-0.5">Stress families</p>
              </div>
              <div>
                <p className="font-manrope font-bold text-2xl md:text-3xl text-white">
                  <CountUp value={7} decimals={0} />
                </p>
                <p className="font-inter text-xs text-white/50 mt-0.5">Supported models</p>
              </div>
              <div>
                <p className="font-manrope font-bold text-2xl md:text-3xl text-white">
                  Seeded
                </p>
                <p className="font-inter text-xs text-white/50 mt-0.5">Reproducible runs</p>
              </div>
              <div>
                <p className="font-manrope font-bold text-2xl md:text-3xl text-white">
                  Research
                </p>
                <p className="font-inter text-xs text-white/50 mt-0.5">Grade analysis</p>
              </div>
            </motion.div>
          </div>

          {/* Right Column: Rotating 3D Brain (~55% on desktop, bleeding to right edge) */}
          <div className="lg:col-span-6 xl:col-span-7 flex justify-center lg:justify-end xl:translate-x-8">
            <RotatingBrain />
          </div>
        </div>
      </section>

      {/* Feature Spotlight Section (#features) - Video Showcase */}
      <FeatureSpotlight />

      {/* Section 1: How It Works (#how-it-works) */}
      <section
        id="how-it-works"
        className="py-32 px-6 md:px-12 xl:px-[120px] border-t border-white/8 relative overflow-hidden z-10"
      >
        <div className="max-w-[1440px] mx-auto space-y-20 relative">
          <Reveal className="text-center max-w-2xl mx-auto space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 font-mono text-xs tracking-widest uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
              <span>EXECUTION PIPELINE</span>
            </div>
            <h2 className="font-manrope font-bold text-3xl sm:text-4xl md:text-5xl text-white tracking-tight">
              Five steps from baseline to autopsy
            </h2>
            <p className="font-inter text-sm md:text-base text-white/60 leading-relaxed">
              Every experiment strictly isolates training and evaluation, applying controlled perturbations only to validation splits.
            </p>
          </Reveal>

          {/* Connected 5-Step Pipeline Grid */}
          <div className="relative">
            {/* Subtle Neon Track Line behind cards on desktop */}
            <div className="hidden lg:block absolute top-1/2 -translate-y-1/2 left-8 right-8 h-[2px] bg-gradient-to-r from-transparent via-sky-500/25 to-transparent pointer-events-none z-0" />

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5 relative z-10">
              {[
                {
                  step: '01',
                  phase: 'INGEST',
                  title: 'Dataset Split',
                  desc: 'Select standard benchmarks or upload clean custom CSV evaluation splits.',
                  tag: 'CSV & OpenML',
                  icon: Database,
                },
                {
                  step: '02',
                  phase: 'ADAPT',
                  title: 'Model Adapter',
                  desc: 'Choose from 7 verified scikit-learn classification & regression adapters.',
                  tag: '7 Estimators',
                  icon: Cpu,
                },
                {
                  step: '03',
                  phase: 'GROUND',
                  title: 'Clean Baseline',
                  desc: 'Establish clean ground-truth metrics and evaluate clean confusion matrices.',
                  tag: 'Zero-Noise Floor',
                  icon: Gauge,
                },
                {
                  step: '04',
                  phase: 'STRESS',
                  title: 'Stress Injection',
                  desc: 'Configure Gaussian Noise, Missingness, and multi-severity perturbation tiers.',
                  tag: 'Severity Tiers',
                  icon: Zap,
                },
                {
                  step: '05',
                  phase: 'ANALYZE',
                  title: 'Manifest Review',
                  desc: 'Validate declarative experiment YAML manifests and launch evaluation.',
                  tag: 'SHA-256 Provenance',
                  icon: FileCheck2,
                },
              ].map((item, idx) => {
                const Icon = item.icon;
                return (
                  <Reveal key={item.step} delay={idx * 0.08}>
                    <div className="p-6 h-full flex flex-col justify-between space-y-5 rounded-2xl bg-[#090b14]/85 backdrop-blur-xl border border-white/12 shadow-[0_12px_30px_rgba(0,0,0,0.6)] hover:border-sky-400/50 hover:bg-[#0d1020] hover:shadow-[0_16px_40px_rgba(56,189,248,0.15)] transition-all duration-300 hover:-translate-y-2 group relative overflow-hidden">
                      {/* Top ambient highlight on hover */}
                      <div className="absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-sky-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs font-bold text-sky-400/80 px-2 py-0.5 rounded bg-sky-500/10 border border-sky-500/20">
                            {item.step} // {item.phase}
                          </span>
                          <div className="p-2.5 rounded-xl bg-surface-2 border border-white/10 text-white/80 group-hover:border-sky-400/40 group-hover:bg-sky-500/15 group-hover:text-sky-300 transition-all duration-200 shadow-sm">
                            <Icon className="w-4 h-4" />
                          </div>
                        </div>

                        <div>
                          <h3 className="font-manrope font-bold text-lg text-white group-hover:text-sky-100 transition-colors">
                            {item.title}
                          </h3>
                          <p className="font-inter text-xs text-white/60 leading-relaxed mt-2">
                            {item.desc}
                          </p>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-white/8 flex items-center justify-between">
                        <span className="font-mono text-[10px] text-sky-400/70 uppercase tracking-wider font-semibold">
                          {item.tag}
                        </span>
                        <span className="w-1.5 h-1.5 rounded-full bg-white/20 group-hover:bg-sky-400 group-hover:shadow-[0_0_6px_#38bdf8] transition-colors" />
                      </div>
                    </div>
                  </Reveal>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Stress Tests (#stress-tests) */}
      <section
        id="stress-tests"
        className="py-32 px-6 md:px-12 xl:px-[120px] border-t border-white/8 relative overflow-hidden z-10"
      >
        <div className="max-w-[1440px] mx-auto space-y-20">
          <Reveal className="text-center max-w-2xl mx-auto space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 font-mono text-xs tracking-widest uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
              <span>PERTURBATION MODULES</span>
            </div>
            <h2 className="font-manrope font-bold text-3xl sm:text-4xl md:text-5xl text-white tracking-tight">
              Five Stress Families
            </h2>
            <p className="font-inter text-sm md:text-base text-white/60 leading-relaxed">
              Targeted failure simulation against sensor corruption, missing telemetries, and distributional decay.
            </p>
          </Reveal>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-5">
            {[
              {
                name: 'Gaussian Noise',
                desc: 'Adds scaled normal perturbations proportional to feature variance.',
                math: 'σ ~ N(0, σ²)',
                status: 'Available',
                isAvailable: true,
              },
              {
                name: 'Missingness',
                desc: 'Simulates missing values (MCAR, MAR) across feature subsets.',
                math: 'P(M|X) Dropout',
                status: 'Available',
                isAvailable: true,
              },
              {
                name: 'Outliers',
                desc: 'Injects heavy-tailed anomalous extreme observations.',
                math: '|z| > 3.5σ Spikes',
                status: 'Queued',
                isAvailable: false,
              },
              {
                name: 'Feature Corruption',
                desc: 'Swaps categories and corrupts discrete token encodings.',
                math: 'Swap(C_i, C_j)',
                status: 'Queued',
                isAvailable: false,
              },
              {
                name: 'Distribution Shift',
                desc: 'Simulates covariate drift and continuous concept drift.',
                math: 'P_t(X) ≠ P_0(X)',
                status: 'Queued',
                isAvailable: false,
              },
            ].map((stress, idx) => (
              <Reveal key={stress.name} delay={idx * 0.08}>
                <div className="p-6 h-full flex flex-col justify-between space-y-5 rounded-2xl bg-[#090b14]/85 backdrop-blur-xl border border-white/12 shadow-[0_12px_30px_rgba(0,0,0,0.6)] hover:border-sky-400/50 hover:bg-[#0d1020] hover:shadow-[0_16px_40px_rgba(56,189,248,0.15)] transition-all duration-300 hover:-translate-y-2 group relative overflow-hidden">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      {stress.isAvailable ? (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[10px] font-mono font-semibold uppercase shadow-[0_0_10px_rgba(52,211,153,0.15)]">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                          <span>{stress.status}</span>
                        </div>
                      ) : (
                        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-white/50 text-[10px] font-mono uppercase">
                          <span>{stress.status}</span>
                        </div>
                      )}

                      <span className="font-mono text-[10px] text-sky-400/70 font-semibold px-2 py-0.5 rounded bg-white/5">
                        MOD-0{idx + 1}
                      </span>
                    </div>

                    <div>
                      <h3 className="font-manrope font-bold text-lg text-white group-hover:text-sky-200 transition-colors">
                        {stress.name}
                      </h3>
                      <p className="font-inter text-xs text-white/60 leading-relaxed mt-2">
                        {stress.desc}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/8 flex items-center justify-between">
                    <span className="font-mono text-[11px] text-sky-300/80 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/20">
                      {stress.math}
                    </span>
                    <Sparkles className="w-3.5 h-3.5 text-white/30 group-hover:text-sky-400 transition-colors" />
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Section 3: Results Preview (#results) */}
      <section
        id="results"
        className="py-32 px-6 md:px-12 xl:px-[120px] border-t border-white/8 relative overflow-hidden z-10"
      >
        <div className="max-w-[1440px] mx-auto space-y-16">
          <Reveal className="text-center max-w-2xl mx-auto space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-400/30 text-sky-400 font-mono text-xs tracking-widest uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
              <span>INTERACTIVE TELEMETRY DECK</span>
            </div>
            <h2 className="font-manrope font-bold text-3xl sm:text-4xl md:text-5xl text-white tracking-tight">
              Instant failure discovery & boundaries
            </h2>
            <p className="font-inter text-sm md:text-base text-white/60 leading-relaxed">
              Explore actual degradation curves, boundary thresholds, and per-sample feature breakdowns.
            </p>
          </Reveal>

          {/* Research Terminal Workstation Container */}
          <Reveal delay={0.2}>
            <div className="relative rounded-[28px] p-2 sm:p-3 bg-gradient-to-b from-[#131622]/90 via-[#0a0c14]/90 to-[#06070a]/95 backdrop-blur-2xl border border-white/15 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.9),0_0_50px_rgba(56,189,248,0.15)]">
              {/* Terminal Top Status Bar */}
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10 mb-2 select-none">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                  <span className="font-mono text-[10px] text-white/60 ml-2 tracking-wider uppercase font-semibold">
                    AUTOPSY_DECK_v2.4 // TELEMETRY_SIMULATOR
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[9px] text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/25 tracking-widest uppercase font-semibold">
                    ● TELEMETRY STREAM ONLINE
                  </span>
                </div>
              </div>

              {/* Core Results Preview Component */}
              <div className="p-2 sm:p-4">
                <ResultsPreview />
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* Section 4: Honest-Claims Strip */}
      <section className="py-24 px-6 md:px-12 xl:px-[120px] border-t border-white/8 relative z-10">
        <div className="max-w-[1440px] mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-start gap-5 p-6 rounded-2xl bg-[#090b14]/85 backdrop-blur-xl border border-white/12 border-t-2 border-t-emerald-400/60 shadow-lg hover:border-emerald-400/40 transition-colors">
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 mt-1 shadow-[0_0_15px_rgba(52,211,153,0.15)]">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-manrope font-bold text-lg text-white">
                Controlled experiments
              </h3>
              <p className="font-inter text-xs sm:text-sm text-white/60 mt-1.5 leading-relaxed">
                Stress is applied strictly to evaluation splits. The model and its training features remain entirely pristine.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-5 p-6 rounded-2xl bg-[#090b14]/85 backdrop-blur-xl border border-white/12 border-t-2 border-t-sky-400/60 shadow-lg hover:border-sky-400/40 transition-colors">
            <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/25 text-sky-400 mt-1 shadow-[0_0_15px_rgba(56,189,248,0.15)]">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-manrope font-bold text-lg text-white">
                Seeded & reproducible
              </h3>
              <p className="font-inter text-xs sm:text-sm text-white/60 mt-1.5 leading-relaxed">
                Deterministic seeds and strict manifest tracking guarantee byte-for-byte reproducibility across runs.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-5 p-6 rounded-2xl bg-[#090b14]/85 backdrop-blur-xl border border-white/12 border-t-2 border-t-amber-400/60 shadow-lg hover:border-amber-400/40 transition-colors">
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-400 mt-1 shadow-[0_0_15px_rgba(245,158,11,0.15)]">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-manrope font-bold text-lg text-white">
                Observed boundaries
              </h3>
              <p className="font-inter text-xs sm:text-sm text-white/60 mt-1.5 leading-relaxed">
                Observed failure boundary under the specified experimental configuration — honest empirical limits, never universal claims.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Section 5: Final CTA Band */}
      <section className="py-28 px-6 md:px-12 xl:px-[120px] border-t border-white/8 relative overflow-hidden z-10">
        <div className="max-w-3xl mx-auto text-center space-y-6">
          <h2 className="font-serif text-4xl md:text-6xl text-white">
            Run your first autopsy
          </h2>
          <p className="font-inter text-sm md:text-base text-white/60 max-w-xl mx-auto leading-relaxed">
            Test classification and regression models against synthetic or custom stress distributions in minutes.
          </p>
          <div className="pt-2">
            <Link
              href="/workspace"
              className="inline-flex items-center justify-center gap-2.5 h-12 px-8 rounded-full bg-white text-black font-manrope font-semibold text-base shadow-[0_0_30px_rgba(255,255,255,0.25)] hover:bg-[#eaeaea] hover:shadow-[0_0_40px_rgba(255,255,255,0.4)] transition-all duration-200 hover:scale-[1.02] active:scale-[0.98] group"
            >
              <span>Launch Autopsy Workspace</span>
              <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 md:px-12 xl:px-[120px] border-t border-white/8 bg-bg text-xs text-text-subtle">
        <div className="max-w-[1440px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-6">
          <Logo size="sm" />
          <div className="flex items-center gap-6">
            <Link href="#features" className="hover:text-white transition-colors">
              Features
            </Link>
            <Link href="#how-it-works" className="hover:text-white transition-colors">
              How it works
            </Link>
            <Link href="#stress-tests" className="hover:text-white transition-colors">
              Stress Tests
            </Link>
            <Link href="/docs" className="hover:text-white transition-colors">
              Docs
            </Link>
            <Link href="/dev/ui" className="hover:text-white transition-colors">
              Dev Lab
            </Link>
          </div>
          <p>© {new Date().getFullYear()} Model Autopsy. Research-grade ML robustness testing.</p>
        </div>
      </footer>
    </div>
  );
}
