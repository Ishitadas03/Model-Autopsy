'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { FileText, ArrowRight, Calendar } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { api } from '@/lib/api';
import { Experiment } from '@/lib/schemas';

function formatReportDate(isoString?: string | null): string {
  if (!isoString) return 'Recent';
  try {
    const cleaned = isoString.replace(/\+00:00Z$/, 'Z').replace(/\+00:00$/, 'Z');
    const d = new Date(cleaned);
    if (isNaN(d.getTime())) return isoString.split('T')[0] || 'Recent';
    return d.toLocaleDateString();
  } catch {
    return 'Recent';
  }
}

export default function ReportsDirectoryPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getExperiments();
      if (Array.isArray(data)) {
        setExperiments(data);
      } else {
        setExperiments([]);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load report directory');
    } finally {
      setLoading(false);
    }
  };

  const completed = experiments.filter((e) => e && (e.status === 'completed' || e.results));

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

        {/* Reports Content */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="p-5 rounded-xl bg-surface border border-border space-y-3">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-16 w-full rounded-lg" />
              </div>
            ))}
          </div>
        ) : error ? (
          <ErrorState
            title="Failed to load reports"
            message={error}
            onRetry={loadReports}
          />
        ) : completed.length === 0 ? (
          <EmptyState
            title="No completed reports yet"
            description="Run and complete stress-test autopsies to view and export formal research reports."
            actionLabel="Run New Autopsy"
            onAction={() => window.location.assign('/workspace')}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {completed.map((exp) => {
              const boundary = exp.results?.observedBoundary;
              const worstF1 =
                exp.results?.worstCaseMetrics?.f1 ??
                exp.results?.worstCaseMetrics?.[exp.metric] ??
                (exp.results as any)?.worstCaseScore;

              return (
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
                        Dataset: {exp.datasetName} · Perturbation: {exp.noiseType || exp.perturbationFamily || 'Stress Test'}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs font-mono p-3 rounded-lg bg-surface-2 border border-border">
                      <div>
                        <span className="text-[10px] text-text-subtle block">Observed Boundary</span>
                        <span className="text-accent font-bold">
                          {boundary !== undefined && boundary !== null
                            ? `${(Number(boundary) * 100).toFixed(1)}%`
                            : 'N/A'}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-text-subtle block">Worst-Case Score</span>
                        <span className="text-white font-bold">
                          {worstF1 !== undefined && worstF1 !== null
                            ? `${(Number(worstF1) * 100).toFixed(1)}%`
                            : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-[11px] text-text-subtle font-mono">
                      <Calendar className="w-3 h-3" />
                      <span>{formatReportDate(exp.createdAt)}</span>
                    </div>

                    <Link href={`/experiments/${exp.id}/report`}>
                      <Button variant="secondary" size="sm" className="gap-1.5 text-xs">
                        <span>View Formal Report</span>
                        <ArrowRight className="w-3 h-3" />
                      </Button>
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
