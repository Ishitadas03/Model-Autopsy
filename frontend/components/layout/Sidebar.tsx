'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  Plus,
  LayoutDashboard,
  FlaskConical,
  Database,
  Cpu,
  Activity,
  AlertTriangle,
  Sliders,
  Compass,
  FileText,
} from 'lucide-react';

interface SidebarProps {
  className?: string;
  experimentId?: string;
}

export function Sidebar({ className = '', experimentId }: SidebarProps) {
  const pathname = usePathname();

  const mainItems = [
    { label: 'Overview', href: '/experiments', icon: LayoutDashboard },
    { label: 'Experiments', href: '/experiments', icon: FlaskConical },
    { label: 'Datasets', href: '/datasets', icon: Database },
    { label: 'Models', href: '/models', icon: Cpu },
  ];

  // Contextual analysis links if we are inside an experiment, or fallback to EXP-0241
  const expMatch = pathname ? pathname.match(/\/experiments\/([^/]+)/) : null;
  const currentExpId = experimentId || (expMatch ? expMatch[1] : 'EXP-0241');
  const expBase = `/experiments/${currentExpId}`;

  const analysisItems = [
    { label: 'Robustness', href: `${expBase}/results`, icon: Activity },
    { label: 'Failures', href: `${expBase}/failures`, icon: AlertTriangle },
    { label: 'Features', href: `${expBase}/results?tab=features`, icon: Sliders },
    { label: 'Boundary', href: `${expBase}/results?tab=boundary`, icon: Compass },
  ];

  const reportItems = [
    { label: 'Generated Reports', href: `${expBase}/report`, icon: FileText },
  ];

  return (
    <aside
      className={`w-64 flex-shrink-0 bg-[#060812]/85 backdrop-blur-2xl border-r border-white/10 p-4 flex flex-col justify-between hidden md:flex ${className}`}
    >
      <div className="space-y-6">
        {/* Outlined New Autopsy button */}
        <Link
          href="/workspace"
          className="flex items-center justify-center gap-2 w-full py-2.5 px-3 rounded-xl bg-white/5 border border-white/15 hover:border-sky-400/50 hover:bg-sky-500/10 hover:shadow-[0_0_20px_rgba(56,189,248,0.2)] transition-all text-xs font-manrope font-semibold text-white group"
        >
          <Plus className="w-3.5 h-3.5 text-sky-400 transition-transform group-hover:rotate-90 duration-200" />
          <span>New Autopsy</span>
        </Link>

        {/* Primary nav group */}
        <div className="space-y-1">
          {mainItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-manrope font-medium transition-all ${
                  isActive
                    ? 'bg-sky-500/10 text-white font-semibold border border-sky-500/20 shadow-[inset_0_0_12px_rgba(56,189,248,0.1)]'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebarActive"
                    className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-sky-400 shadow-[0_0_8px_#38bdf8] rounded-r"
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-white/40'}`} aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Analysis Section */}
        <div className="space-y-1">
          <p className="px-3 text-[10px] font-mono uppercase tracking-widest text-white/40 mb-1">
            Analysis
          </p>
          {analysisItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-manrope font-medium transition-all ${
                  isActive
                    ? 'bg-sky-500/10 text-white font-semibold border border-sky-500/20 shadow-[inset_0_0_12px_rgba(56,189,248,0.1)]'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebarActive"
                    className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-sky-400 shadow-[0_0_8px_#38bdf8] rounded-r"
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-white/40'}`} aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Reports Section */}
        <div className="space-y-1">
          <p className="px-3 text-[10px] font-mono uppercase tracking-widest text-white/40 mb-1">
            Reports
          </p>
          {reportItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-manrope font-medium transition-all ${
                  isActive
                    ? 'bg-sky-500/10 text-white font-semibold border border-sky-500/20 shadow-[inset_0_0_12px_rgba(56,189,248,0.1)]'
                    : 'text-white/60 hover:text-white hover:bg-white/5'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebarActive"
                    className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-sky-400 shadow-[0_0_8px_#38bdf8] rounded-r"
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-white/40'}`} aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="pt-4 border-t border-white/8 text-[11px] text-white/40">
        <p className="font-mono uppercase tracking-wider text-[10px] text-sky-400/80 font-semibold">
          Model Autopsy Lab
        </p>
        <p className="mt-0.5">Seeded reproducible runs</p>
      </div>
    </aside>
  );
}
