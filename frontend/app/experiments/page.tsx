'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  RotateCw,
  SlidersHorizontal,
  ChevronRight,
  Database,
  Cpu,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { api } from '@/lib/api';
import { Experiment } from '@/lib/schemas';
import { StatusPill } from '@/components/ui/StatusPill';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Dialog } from '@/components/ui/Dialog';
import { useToast } from '@/components/ui/Toast';

export default function ExperimentsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [datasetFilter, setDatasetFilter] = useState('all');

  // Rerun modal state
  const [rerunTarget, setRerunTarget] = useState<Experiment | null>(null);
  const [isRerunning, setIsRerunning] = useState(false);

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getExperiments();
      setExperiments(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load experiments');
    } finally {
      setLoading(false);
    }
  };

  const filtered = experiments.filter((exp) => {
    if (statusFilter !== 'all' && exp.status !== statusFilter) return false;
    if (datasetFilter !== 'all' && exp.datasetId !== datasetFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        exp.id.toLowerCase().includes(q) ||
        exp.title.toLowerCase().includes(q) ||
        exp.modelName.toLowerCase().includes(q) ||
        exp.datasetName.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const uniqueDatasets = Array.from(new Set(experiments.map((e) => e.datasetId)));

  const handleConfirmRerun = async () => {
    if (!rerunTarget) return;
    setIsRerunning(true);
    try {
      const newRun = await api.createExperiment({
        title: `${rerunTarget.title} (Re-run)`,
        datasetId: rerunTarget.datasetId,
        datasetName: rerunTarget.datasetName,
        modelId: rerunTarget.modelId,
        modelName: rerunTarget.modelName,
        taskType: rerunTarget.taskType,
        stressConfig: rerunTarget.stressConfig,
        metric: rerunTarget.metric,
        failureThreshold: rerunTarget.failureThreshold,
        testSize: rerunTarget.testSize,
        seed: rerunTarget.seed,
        numSeeds: rerunTarget.numSeeds,
      });

      toast({
        type: 'success',
        title: 'Re-run Triggered',
        message: `Created experiment ${newRun.id} with identical seed ${rerunTarget.seed}.`,
      });

      setRerunTarget(null);
      router.push(`/experiments/${newRun.id}`);
    } finally {
      setIsRerunning(false);
    }
  };

  return (
    <AppShell showSidebar>
      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div>
            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white tracking-tight">
              Experiments
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-1">
              Track, inspect, and reproduce model robustness stress tests.
            </p>
          </div>

          <Link href="/workspace">
            <Button variant="primary" className="gap-2">
              <Plus className="w-4 h-4" />
              <span>New Autopsy</span>
            </Button>
          </Link>
        </div>

        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between bg-surface p-3.5 rounded-xl border border-border">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 text-text-subtle absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search by ID, title, model..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-surface-2 border border-border text-xs text-white placeholder-text-subtle focus:outline-none focus:border-white/40"
            />
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-surface-2 border border-border rounded-lg px-3 py-1.5 text-xs text-white font-cabin focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="running">Running</option>
              <option value="queued">Queued</option>
              <option value="draft">Draft</option>
              <option value="failed">Failed</option>
            </select>

            <select
              value={datasetFilter}
              onChange={(e) => setDatasetFilter(e.target.value)}
              className="bg-surface-2 border border-border rounded-lg px-3 py-1.5 text-xs text-white font-cabin focus:outline-none"
            >
              <option value="all">All Datasets</option>
              {uniqueDatasets.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>

            <Button
              variant="secondary"
              size="sm"
              onClick={loadExperiments}
              className="p-2"
              title="Refresh experiments"
            >
              <RotateCw className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        {/* Content State */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="p-5 rounded-xl bg-surface border border-border flex items-center justify-between"
              >
                <div className="space-y-2">
                  <Skeleton className="h-4 w-40" />
                  <Skeleton className="h-3 w-72" />
                </div>
                <Skeleton className="h-8 w-24 rounded-full" />
              </div>
            ))}
          </div>
        ) : error ? (
          <ErrorState
            title="Failed to load experiments"
            message={error}
            onRetry={loadExperiments}
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No experiments found"
            description="Try adjusting your search query or filter settings, or configure a new autopsy."
            actionLabel="Start New Autopsy"
            onAction={() => router.push('/workspace')}
          />
        ) : (
          <div className="space-y-3">
            {filtered.map((exp) => {
              const degradation = exp.results
                ? (
                    (exp.results.worstCaseMetrics[exp.metric] || 0) * 100 -
                    (exp.results.baselineMetrics[exp.metric] || 0) * 100
                  ).toFixed(1)
                : null;

              return (
                <div
                  key={exp.id}
                  className="p-5 rounded-xl bg-surface border border-border hover:border-border-strong transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 group"
                >
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="font-mono text-xs text-accent font-semibold px-2 py-0.5 rounded bg-accent/10 border border-accent/20">
                        {exp.id}
                      </span>
                      <h3 className="font-manrope font-semibold text-sm text-white group-hover:text-accent transition-colors">
                        {exp.title}
                      </h3>
                      <StatusPill status={exp.status} />
                    </div>

                    <div className="flex items-center gap-4 text-xs text-text-subtle font-manrope flex-wrap">
                      <span className="flex items-center gap-1.5">
                        <Database className="w-3.5 h-3.5" />
                        {exp.datasetName}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Cpu className="w-3.5 h-3.5" />
                        {exp.modelName}
                      </span>
                      <span className="font-mono">
                        Seed: {exp.seed}
                      </span>
                      <span className="flex items-center gap-1 text-[11px] text-text-subtle/80">
                        <Clock className="w-3 h-3" />
                        {new Date(exp.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 self-end md:self-center">
                    {degradation && (
                      <div className="text-right">
                        <div className="text-[11px] text-text-subtle font-cabin uppercase">
                          Degradation
                        </div>
                        <div className="font-mono text-xs font-semibold text-accent">
                          {degradation} pp
                        </div>
                      </div>
                    )}

                    <div className="flex items-center gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setRerunTarget(exp)}
                        className="gap-1.5 text-xs"
                      >
                        <RotateCw className="w-3.5 h-3.5" />
                        <span>Rerun</span>
                      </Button>

                      <Link
                        href={
                          exp.status === 'completed'
                            ? `/experiments/${exp.id}/results`
                            : `/experiments/${exp.id}`
                        }
                      >
                        <Button variant="primary" size="sm" className="gap-1 text-xs">
                          <span>{exp.status === 'completed' ? 'Results' : 'Inspect'}</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Rerun Confirmation Dialog */}
        <Dialog
          open={!!rerunTarget}
          onClose={() => setRerunTarget(null)}
          title="Confirm Reproducible Re-run"
          description={`Execute a fresh stress test run for ${rerunTarget?.id} using identical seed (${rerunTarget?.seed}) and configuration parameters.`}
        >
          <div className="space-y-4 pt-2">
            <div className="p-3.5 rounded-lg bg-surface-2 border border-border text-xs text-text-muted space-y-1 font-mono">
              <div>Dataset: {rerunTarget?.datasetName}</div>
              <div>Model: {rerunTarget?.modelName}</div>
              <div>Seed: {rerunTarget?.seed}</div>
              <div>Metric: {rerunTarget?.metric}</div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setRerunTarget(null)}
                disabled={isRerunning}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleConfirmRerun}
                loading={isRerunning}
                className="gap-1.5"
              >
                <RotateCw className="w-3.5 h-3.5" />
                <span>Execute Re-run</span>
              </Button>
            </div>
          </div>
        </Dialog>
      </div>
    </AppShell>
  );
}
