'use client';

import React from 'react';
import Link from 'next/link';
import { FileText, ArrowRight, ShieldCheck, Calendar, Activity } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { MOCK_EXPERIMENTS } from '@/lib/mocks/experiments';

export default function ReportsDirectoryPage() {
  const completedExperiments = MOCK_EXPERIMENTS.filter((e) => e.status === 'completed');

  return (
    <AppShell showSidebar>
      <div className="max-w-5xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-accent font-semibold px-2 py-0.5 rounded bg-accent/10 border border-accent/20">
                Reports Directory
              </span>
              <span className="text-xs text-text-subtle font-mono">Formal Evaluations</span>
            </div>
            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white tracking-tight">
              Generated Research Reports
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-0.5">
              Comprehensive stress-test autopsy records with empirical boundaries, degradation curves, and audit trails.
            </p>
          </div>

          <Link href="/workspace">
            <Button variant="primary" size="sm" className="gap-1.5 text-xs">
              <span>Run New Autopsy</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </div>

        {/* Reports Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {completedExperiments.map((exp) => (
            <div
              key={exp.id}
              className="p-5 rounded-xl bg-surface border border-border hover:border-white/20 transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-accent" />
                    <span className="font-mono text-xs font-bold text-white">{exp.id}</span>
                  </div>
                  <Badge variant="accent" size="sm">
                    {exp.taskType}
                  </Badge>
                </div>

                <div>
                  <h3 className="font-manrope font-semibold text-base text-white">
                    {exp.modelName}
                  </h3>
                  <p className="text-xs text-text-subtle mt-0.5 font-cabin">
                    Dataset: {exp.datasetName} · Perturbation: {exp.stressConfig?.type || 'Gaussian Noise'}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono p-3 rounded-lg bg-surface-2 border border-border">
                  <div>
                    <span className="text-[10px] text-text-subtle block">Observed Boundary</span>
                    <span className="text-accent font-bold">
                      {exp.results?.observedBoundary ? `${(exp.results.observedBoundary * 100).toFixed(1)}%` : '23.1%'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-text-subtle block">Worst-Case F1</span>
                    <span className="text-white font-bold">
                      {exp.results?.worstCaseMetrics?.f1 ? `${(exp.results.worstCaseMetrics.f1 * 100).toFixed(1)}%` : '71.2%'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-[11px] text-text-subtle font-mono">
                  <Calendar className="w-3 h-3" />
                  <span>{new Date(exp.createdAt).toLocaleDateString()}</span>
                </div>

                <Link href={`/experiments/${exp.id}/report`}>
                  <Button variant="secondary" size="sm" className="gap-1.5 text-xs">
                    <span>View Formal Report</span>
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
