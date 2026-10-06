'use client';

import React from 'react';
import Link from 'next/link';
import { Sliders, ArrowRight } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

interface StressProfile {
  id: string;
  name: string;
  family: string;
  description: string;
  defaultSeverities: number[];
}

const STRESS_PROFILES: StressProfile[] = [
  {
    id: 'gaussian_noise',
    name: 'Zero-Mean Gaussian Noise',
    family: 'Additive Noise',
    description: 'Injects normal-distribution perturbations scaled relative to each feature standard deviation.',
    defaultSeverities: [0.05, 0.1, 0.2, 0.3],
  },
  {
    id: 'salt_and_pepper',
    name: 'Salt & Pepper Perturbation',
    family: 'Extreme Outliers',
    description: 'Randomly resets feature values to observed empirical minimums or maximums.',
    defaultSeverities: [0.02, 0.05, 0.1, 0.2],
  },
  {
    id: 'missing_features',
    name: 'Simulated Missing Values',
    family: 'Erasure Drift',
    description: 'Replaces selected feature values with mean or median defaults to evaluate sensor blackout resilience.',
    defaultSeverities: [0.05, 0.1, 0.2, 0.3],
  },
  {
    id: 'scaling_drift',
    name: 'Covariate Scale Shift',
    family: 'Multiplicative Drift',
    description: 'Systematically scales feature distributions up or down to simulate temporal inflation or unit changes.',
    defaultSeverities: [0.1, 0.2, 0.3, 0.5],
  },
];

export default function StressTestsCatalogPage() {
  return (
    <AppShell showSidebar>
      <div className="max-w-5xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-accent font-semibold px-2 py-0.5 rounded bg-accent/10 border border-accent/20">
                Perturbation Catalog
              </span>
              <span className="text-xs text-text-subtle font-mono">Stress Protocols</span>
            </div>
            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white tracking-tight">
              Stress Test Protocols
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-0.5">
              Controlled synthetic distribution shifts applied to hold-out evaluation splits for failure boundary profiling.
            </p>
          </div>

          <Link href="/workspace">
            <Button variant="primary" size="sm" className="gap-1.5 text-xs">
              <span>Configure in Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </div>

        {/* Profiles Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {STRESS_PROFILES.map((profile) => (
            <div
              key={profile.id}
              className="p-5 rounded-xl bg-surface border border-border hover:border-white/20 transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-accent" />
                    <h3 className="font-manrope font-semibold text-base text-white">
                      {profile.name}
                    </h3>
                  </div>
                  <Badge variant="accent" size="sm">
                    {profile.family}
                  </Badge>
                </div>

                <p className="text-xs text-text-muted font-cabin leading-relaxed">
                  {profile.description}
                </p>

                <div className="p-3 rounded-lg bg-surface-2 border border-border space-y-1.5 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-text-subtle">Default Severities:</span>
                    <span className="text-white">[{profile.defaultSeverities.map((s) => `${Math.round(s * 100)}%`).join(', ')}]</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-subtle">Target Features:</span>
                    <span className="text-white">All Numeric Features</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                <span className="text-[11px] text-text-subtle font-mono">
                  Deterministic random seed calibrated
                </span>

                <Link href="/workspace">
                  <Button variant="secondary" size="sm" className="gap-1.5 text-xs">
                    <span>Use Protocol</span>
                    <ArrowRight className="w-3 h-3" />
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
