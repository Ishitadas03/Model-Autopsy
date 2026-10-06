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
      className={`w-64 flex-shrink-0 bg-surface/50 border-r border-border p-4 flex flex-col justify-between hidden md:flex ${className}`}
    >
      <div className="space-y-6">
        {/* Outlined New Autopsy button */}
        <Link
          href="/workspace"
          className="flex items-center justify-center gap-2 w-full py-2 px-3 rounded-[10px] border border-white/25 hover:border-white/60 hover:bg-white/5 transition-all text-xs font-cabin font-medium text-white group"
        >
          <Plus className="w-3.5 h-3.5 text-accent transition-transform group-hover:rotate-90 duration-200" />
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
                className={`relative flex items-center gap-3 px-3 py-2 rounded-[8px] text-xs font-manrope font-medium transition-colors ${
                  isActive
                    ? 'bg-surface-2 text-white'
                    : 'text-text-muted hover:text-white hover:bg-white/5'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebarActive"
                    className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-white rounded-r"
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
                <Icon className="w-4 h-4 text-text-subtle" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Analysis Section */}
        <div className="space-y-1">
          <p className="px-3 text-[10px] font-cabin uppercase tracking-widest text-text-subtle mb-1">
            Analysis
          </p>
          {analysisItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex items-center gap-3 px-3 py-2 rounded-[8px] text-xs font-manrope font-medium transition-colors ${
                  isActive
                    ? 'bg-surface-2 text-white'
                    : 'text-text-muted hover:text-white hover:bg-white/5'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebarActive"
                    className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-white rounded-r"
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
                <Icon className="w-4 h-4 text-text-subtle" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Reports Section */}
        <div className="space-y-1">
          <p className="px-3 text-[10px] font-cabin uppercase tracking-widest text-text-subtle mb-1">
            Reports
          </p>
          {reportItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex items-center gap-3 px-3 py-2 rounded-[8px] text-xs font-manrope font-medium transition-colors ${
                  isActive
                    ? 'bg-surface-2 text-white'
                    : 'text-text-muted hover:text-white hover:bg-white/5'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="sidebarActive"
                    className="absolute left-0 top-1.5 bottom-1.5 w-[2px] bg-white rounded-r"
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
                <Icon className="w-4 h-4 text-text-subtle" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="pt-4 border-t border-white/5 text-[11px] text-text-subtle">
        <p className="font-cabin uppercase tracking-wider text-[10px] text-text-subtle/80">
          Model Autopsy Lab
        </p>
        <p className="mt-0.5">Seeded reproducible runs</p>
      </div>
    </aside>
  );
}
