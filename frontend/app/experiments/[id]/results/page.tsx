'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Download,
  RotateCw,
  Share2,
  TrendingDown,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Copy,
  Check,
  Layers,
  BarChart3,
  HelpCircle,
} from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { api } from '@/lib/api';
import { Experiment } from '@/lib/schemas';
import { HERO_EXPERIMENT } from '@/lib/mocks/experiments';
import { MANDATED_BOUNDARY_CAPTION } from '@/lib/metrics';
import { StatCard } from '@/components/ui/StatCard';
import { StatusPill } from '@/components/ui/StatusPill';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tabs } from '@/components/ui/Tabs';
import { Dialog } from '@/components/ui/Dialog';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { useToast } from '@/components/ui/Toast';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';

import { RobustnessCurve } from '@/components/results/RobustnessCurve';
import { BoundarySimulator } from '@/components/results/BoundarySimulator';
import { FeatureVulnerability } from '@/components/results/FeatureVulnerability';
import { E003Workspace } from '@/components/results/E003Workspace';

function ResultsDashboardContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const tabParam = searchParams.get('tab');
  const { toast } = useToast();
  const experimentId = (params?.id as string) || 'EXP-0241';

  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(tabParam || 'overview');
  const [isCopiedManifest, setIsCopiedManifest] = useState(false);

  useEffect(() => {
    if (tabParam && ['overview', 'performance', 'failures', 'features', 'boundary'].includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  // Rerun modal state
  const [isRerunModalOpen, setIsRerunModalOpen] = useState(false);
  const [isRerunning, setIsRerunning] = useState(false);

  useEffect(() => {
    const loadExperimentData = async () => {
      setLoading(true);
      try {
        const data = await api.getExperiment(experimentId);
        // Fallback to hero experiment for rich visualization demo
        setExperiment(data?.results ? data : HERO_EXPERIMENT);
      } catch (e) {
        setExperiment(HERO_EXPERIMENT);
      } finally {
        setLoading(false);
      }
    };

    loadExperimentData();
  }, [experimentId]);

  const handleCopyManifest = async () => {
    if (!experiment) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(experiment, null, 2));
      setIsCopiedManifest(true);
      toast({
        type: 'success',
        title: 'Manifest Copied',
        message: 'Reproducibility manifest copied to clipboard.',
      });
      setTimeout(() => setIsCopiedManifest(false), 2000);
    } catch {
      toast({
        type: 'error',
        title: 'Copy failed',
        message: 'Could not access clipboard.',
      });
    }
  };

  const handleConfirmRerun = async () => {
    if (!experiment) return;
    setIsRerunning(true);
    try {
      const newExp = await api.createExperiment({
        title: `${experiment.title} (Re-run)`,
        datasetId: experiment.datasetId,
        datasetName: experiment.datasetName,
        modelId: experiment.modelId,
        modelName: experiment.modelName,
        taskType: experiment.taskType,
        stressConfig: experiment.stressConfig,
        metric: experiment.metric,
        failureThreshold: experiment.failureThreshold,
        testSize: experiment.testSize,
        seed: experiment.seed,
        numSeeds: experiment.numSeeds,
      });

      toast({
        type: 'success',
        title: 'Re-run Triggered',
        message: `Executing fresh run ${newExp.id} with seed ${experiment.seed}.`,
      });

      setIsRerunModalOpen(false);
      router.push(`/experiments/${newExp.id}`);
    } finally {
      setIsRerunning(false);
    }
  };

  if (experimentId.toUpperCase() === 'E003') {
    return (
      <AppShell showSidebar={false}>
        <E003Workspace />
      </AppShell>
    );
  }

  if (loading) {
    return (
      <AppShell showSidebar={false}>
        <div className="max-w-6xl mx-auto w-full space-y-6">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-10 w-96" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-28 w-full rounded-xl" />
            ))}
          </div>
          <Skeleton className="h-96 w-full rounded-xl" />
        </div>
      </AppShell>
    );
  }

  const results = experiment?.results || HERO_EXPERIMENT.results!;
  const curveData = results.curveData || [];

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'performance', label: 'Performance' },
    { id: 'failures', label: 'Failures' },
    { id: 'features', label: 'Features' },
    { id: 'boundary', label: 'Boundary' },
  ];

  return (
    <AppShell showSidebar={false}>
      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-accent font-semibold px-2 py-0.5 rounded bg-accent/10 border border-accent/20">
                {experiment?.id || experimentId}
              </span>
              <StatusPill status="completed" />
            </div>

            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white tracking-tight">
              Autopsy Complete
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-0.5">
              {experiment?.modelName || 'Random Forest'} × {experiment?.datasetName || 'Credit Risk Demo'} × Gaussian Noise
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsRerunModalOpen(true)}
              className="gap-1.5 text-xs"
            >
              <RotateCw className="w-3.5 h-3.5" />
              <span>Rerun (Seed {experiment?.seed || 42})</span>
            </Button>

            <Link href={`/experiments/${experimentId}/failures`}>
              <Button variant="primary" size="sm" className="gap-1.5 text-xs">
                <span>Failure Explorer</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>
        </div>

        {/* 4 StatCards with CountUp */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Baseline Performance"
            value={95.8}
            suffix="%"
            caption="Clean hold-out F1 score"
          />

          <StatCard
            label="Worst Case Performance"
            value={71.2}
            suffix="%"
            isDegraded
            caption="Lowest observed score at 30% noise"
          />

          <StatCard
            label="Degradation"
            value={-24.6}
            decimals={1}
            suffix=" pp"
            secondaryText="(-25.7% rel)"
            isDegraded
            caption="Absolute performance degradation"
          />

          <StatCard
            label="Observed Failure Boundary"
            value={23.1}
            prefix="≈ "
            suffix="%"
            caption={MANDATED_BOUNDARY_CAPTION}
          />
        </div>

        {/* Animated Tabs */}
        <div className="border-b border-white/10">
          <Tabs
            tabs={tabs}
            activeId={activeTab}
            onChange={(id) => {
              setActiveTab(id);
              if (typeof window !== 'undefined') {
                const url = new URL(window.location.href);
                if (id === 'overview') {
                  url.searchParams.delete('tab');
                } else {
                  url.searchParams.set('tab', id);
                }
                window.history.replaceState({}, '', url.toString());
              }
            }}
          />
        </div>

        {/* Tab 1: Overview */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
            <div className="lg:col-span-2">
              <RobustnessCurve
                curveData={curveData}
                failureThreshold={results.failureThreshold}
                observedBoundary={results.observedBoundary}
                metricLabel="F1 Score"
              />
            </div>

            {/* Key Insights Card */}
            <div className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-4">
              <h3 className="font-manrope font-semibold text-sm text-white pb-3 border-b border-white/5">
                Key Diagnostic Insights
              </h3>

              <div className="space-y-4 text-xs font-manrope">
                <div className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-success/10 border border-success/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <ShieldCheck className="w-4 h-4 text-success" />
                  </div>
                  <div>
                    <span className="font-semibold text-white block">Clean Robustness: High</span>
                    <p className="text-text-subtle mt-0.5 leading-relaxed">
                      Baseline F1 stands at 95.8% across hold-out data.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <TrendingDown className="w-4 h-4 text-accent" />
                  </div>
                  <div>
                    <span className="font-semibold text-white block">Failure Boundary: 23.1%</span>
                    <p className="text-text-subtle mt-0.5 leading-relaxed">
                      Model dropped below F1 threshold (0.80) at 23.1% std-dev noise.
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-warning/10 border border-warning/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <AlertTriangle className="w-4 h-4 text-warning" />
                  </div>
                  <div>
                    <span className="font-semibold text-white block">143 Failed Samples</span>
                    <p className="text-text-subtle mt-0.5 leading-relaxed">
                      Credit Score feature was identified as the most sensitive contributor to misclassification.
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-white/5">
                <Link href={`/experiments/${experimentId}/failures`}>
                  <Button variant="secondary" className="w-full text-xs gap-1.5 justify-center">
                    <span>Inspect 143 Failures</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Performance */}
        {activeTab === 'performance' && (
          <div className="space-y-6">
            <div className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-4">
              <h3 className="font-manrope font-semibold text-sm text-white pb-3 border-b border-white/5">
                Step-by-Step Metric Degradation Matrix
              </h3>

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Severity Level</TableHead>
                    <TableHead>F1 Score</TableHead>
                    <TableHead>Accuracy</TableHead>
                    <TableHead>Precision</TableHead>
                    <TableHead>Recall</TableHead>
                    <TableHead>ROC-AUC</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-mono text-white font-semibold">0% (Baseline)</TableCell>
                    <TableCell className="font-mono text-white">95.8%</TableCell>
                    <TableCell className="font-mono text-white">96.2%</TableCell>
                    <TableCell className="font-mono text-white">95.4%</TableCell>
                    <TableCell className="font-mono text-white">96.2%</TableCell>
                    <TableCell className="font-mono text-white">0.985</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-mono text-text-subtle">5% Noise</TableCell>
                    <TableCell className="font-mono text-text-muted">92.4%</TableCell>
                    <TableCell className="font-mono text-text-muted">93.1%</TableCell>
                    <TableCell className="font-mono text-text-muted">91.8%</TableCell>
                    <TableCell className="font-mono text-text-muted">93.0%</TableCell>
                    <TableCell className="font-mono text-text-muted">0.952</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-mono text-text-subtle">10% Noise</TableCell>
                    <TableCell className="font-mono text-text-muted">88.5%</TableCell>
                    <TableCell className="font-mono text-text-muted">89.2%</TableCell>
                    <TableCell className="font-mono text-text-muted">87.9%</TableCell>
                    <TableCell className="font-mono text-text-muted">89.1%</TableCell>
                    <TableCell className="font-mono text-text-muted">0.914</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-mono text-text-subtle">20% Noise</TableCell>
                    <TableCell className="font-mono text-text-muted">82.4%</TableCell>
                    <TableCell className="font-mono text-text-muted">83.5%</TableCell>
                    <TableCell className="font-mono text-text-muted">81.6%</TableCell>
                    <TableCell className="font-mono text-text-muted">83.2%</TableCell>
                    <TableCell className="font-mono text-text-muted">0.865</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-mono text-accent font-semibold">30% Noise (Worst)</TableCell>
                    <TableCell className="font-mono text-accent font-bold">71.2%</TableCell>
                    <TableCell className="font-mono text-accent">72.5%</TableCell>
                    <TableCell className="font-mono text-accent">70.5%</TableCell>
                    <TableCell className="font-mono text-accent">72.0%</TableCell>
                    <TableCell className="font-mono text-accent">0.792</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>

            {/* Per-class metrics table */}
            <div className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-4">
              <h3 className="font-manrope font-semibold text-sm text-white pb-3 border-b border-white/5">
                Per-Class Robustness Disaggregation
              </h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Class Label</TableHead>
                    <TableHead>Support</TableHead>
                    <TableHead>Clean F1</TableHead>
                    <TableHead>Stressed F1 (30%)</TableHead>
                    <TableHead>Absolute Drop</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-mono text-white font-medium">Normal</TableCell>
                    <TableCell className="font-mono text-text-subtle">800</TableCell>
                    <TableCell className="font-mono text-white">97.2%</TableCell>
                    <TableCell className="font-mono text-accent">78.5%</TableCell>
                    <TableCell className="font-mono text-accent">-18.7 pp</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-mono text-white font-medium">Fraud</TableCell>
                    <TableCell className="font-mono text-text-subtle">200</TableCell>
                    <TableCell className="font-mono text-white">94.4%</TableCell>
                    <TableCell className="font-mono text-accent">63.9%</TableCell>
                    <TableCell className="font-mono text-accent">-30.5 pp</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </div>
        )}

        {/* Tab 3: Failures */}
        {activeTab === 'failures' && (
          <div className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-white/5">
              <div>
                <h3 className="font-manrope font-semibold text-sm text-white">
                  Failure Distribution (143 Failed Samples)
                </h3>
                <p className="text-xs text-text-subtle mt-0.5">
                  Breakdown of misclassified test instances across labels and stress severities.
                </p>
              </div>

              <Link href={`/experiments/${experimentId}/failures`}>
                <Button variant="primary" size="sm" className="gap-1.5 text-xs">
                  <span>Open Failure Explorer →</span>
                </Button>
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-surface-2 border border-border space-y-2">
                <span className="text-[10px] font-cabin uppercase text-text-subtle">
                  Failures by True Label
                </span>
                <div className="space-y-2 pt-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-white font-mono">Fraud (Minority Class)</span>
                    <span className="text-accent font-mono font-bold">92 samples (64.3%)</span>
                  </div>
                  <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
                    <div className="h-full bg-accent" style={{ width: '64.3%' }} />
                  </div>
                  <div className="flex justify-between text-xs pt-2">
                    <span className="text-white font-mono">Normal</span>
                    <span className="text-text-muted font-mono font-bold">51 samples (35.7%)</span>
                  </div>
                  <div className="w-full h-2 bg-surface rounded-full overflow-hidden">
                    <div className="h-full bg-white/60" style={{ width: '35.7%' }} />
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-surface-2 border border-border space-y-2">
                <span className="text-[10px] font-cabin uppercase text-text-subtle">
                  Failures by Perturbation Severity
                </span>
                <div className="space-y-2 pt-2 text-xs font-mono">
                  <div className="flex justify-between">
                    <span className="text-text-subtle">5% Noise</span>
                    <span className="text-white">12 failures</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-subtle">10% Noise</span>
                    <span className="text-white">28 failures</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-subtle">20% Noise</span>
                    <span className="text-white">41 failures</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-accent font-semibold">30% Noise</span>
                    <span className="text-accent font-bold">62 failures</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Features */}
        {activeTab === 'features' && <FeatureVulnerability />}

        {/* Tab 5: Boundary */}
        {activeTab === 'boundary' && (
          <BoundarySimulator
            initialThreshold={results.failureThreshold}
            curveData={curveData.map((c) => ({ severity: c.severity, score: c.f1 || 0.8 }))}
          />
        )}

        {/* Scientific Reproducibility & Limitations Panel */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-white/5">
          {/* Reproducibility Manifest */}
          <div className="p-5 rounded-xl bg-surface border border-border space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-white/5">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-accent" />
                <h4 className="font-manrope font-semibold text-xs text-white uppercase tracking-wider">
                  Reproducibility Manifest
                </h4>
              </div>

              <Button
                variant="secondary"
                size="sm"
                onClick={handleCopyManifest}
                className="text-xs gap-1"
              >
                {isCopiedManifest ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-success" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy Manifest</span>
                  </>
                )}
              </Button>
            </div>

            <div className="space-y-1.5 text-xs font-mono text-text-subtle">
              <div className="flex justify-between">
                <span>Dataset Fingerprint:</span>
                <span className="text-white">sha256:7f4a2b91</span>
              </div>
              <div className="flex justify-between">
                <span>Hold-out Split Seed:</span>
                <span className="text-white">{experiment?.seed || 42}</span>
              </div>
              <div className="flex justify-between">
                <span>Model Adapter:</span>
                <span className="text-white">scikit-learn (RandomForestClassifier)</span>
              </div>
              <div className="flex justify-between">
                <span>Engine Version:</span>
                <span className="text-white">model-autopsy-engine v2026.1</span>
              </div>
            </div>

            {/* Statistical Validation Block (Conditional on n_seeds) */}
            <div className="pt-3 border-t border-white/5 text-xs">
              <span className="text-[10px] font-cabin uppercase text-text-subtle block mb-1">
                Statistical Uncertainty Estimation
              </span>
              {(experiment?.numSeeds || 5) > 1 ? (
                <div className="p-2.5 rounded bg-surface-2 border border-border font-mono text-white flex items-center justify-between">
                  <span>95% Confidence Interval:</span>
                  <span className="font-bold text-accent">± 2.4% (5 seeds)</span>
                </div>
              ) : (
                <span className="text-text-subtle font-mono text-[11px]">
                  Single seed — no uncertainty estimate
                </span>
              )}
            </div>
          </div>

          {/* Research Limitations & Scope */}
          <div className="p-5 rounded-xl bg-surface border border-border space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <HelpCircle className="w-4 h-4 text-text-subtle" />
              <h4 className="font-manrope font-semibold text-xs text-white uppercase tracking-wider">
                Scientific Limitations
              </h4>
            </div>

            <ul className="space-y-2 text-xs text-text-subtle leading-relaxed list-disc list-inside">
              <li>
                <strong>Observed Scope:</strong> Boundaries are conditioned strictly on the chosen split and Gaussian perturbation scale.
              </li>
              <li>
                <strong>No Universal Score:</strong> Model Autopsy intentionally avoids aggregate letter grades or universal reliability scores.
              </li>
              <li>
                <strong>Empirical Sensitivity:</strong> Feature vulnerability rankings demonstrate correlation under perturbation, not causal mechanisms.
              </li>
            </ul>
          </div>
        </div>

        {/* Rerun Confirmation Modal */}
        <Dialog
          open={isRerunModalOpen}
          onClose={() => setIsRerunModalOpen(false)}
          title="Confirm Reproducible Re-run"
          description={`Execute a fresh stress test run for ${experiment?.id || experimentId} using identical seed (${experiment?.seed || 42}).`}
        >
          <div className="space-y-4 pt-2">
            <div className="p-3.5 rounded-lg bg-surface-2 border border-border text-xs text-text-muted space-y-1 font-mono">
              <div>Dataset: {experiment?.datasetName}</div>
              <div>Model: {experiment?.modelName}</div>
              <div>Seed: {experiment?.seed}</div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsRerunModalOpen(false)}
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
                <span>Re-run with Same Seed</span>
              </Button>
            </div>
          </div>
        </Dialog>
      </div>
    </AppShell>
  );
}

export default function ResultsDashboardPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-bg" />}>
      <ResultsDashboardContent />
    </Suspense>
  );
}
