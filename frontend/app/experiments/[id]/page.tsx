'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Ban,
  ArrowRight,
  RotateCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { useRunStatus } from '@/hooks/useRunStatus';
import { CircularProgressRing } from '@/components/experiments/CircularProgressRing';
import { RunningChecklist } from '@/components/experiments/RunningChecklist';
import { LiveTelemetry } from '@/components/experiments/LiveTelemetry';
import { Button } from '@/components/ui/Button';
import { Dialog } from '@/components/ui/Dialog';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { useToast } from '@/components/ui/Toast';

export default function ExperimentRunningPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const experimentId = (params?.id as string) || 'EXP-0241';

  const {
    experiment,
    loading,
    error,
    progressPercent,
    currentStage,
    elapsedSeconds,
    completedStages,
    cancelRun,
    retryRun,
  } = useRunStatus(experimentId);

  const [isCancelDialogOpen, setIsCancelDialogOpen] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [hasCompletedNotified, setHasCompletedNotified] = useState(false);

  // Auto-transition to results when progress hits 100%
  useEffect(() => {
    if (progressPercent >= 100 && !hasCompletedNotified) {
      setHasCompletedNotified(true);
      toast({
        type: 'success',
        title: 'Autopsy Complete',
        message: 'Stress testing finished successfully. Transitioning to results dashboard...',
      });

      const timer = setTimeout(() => {
        router.push(`/experiments/${experimentId}/results`);
      }, 1200);

      return () => clearTimeout(timer);
    }
  }, [progressPercent, hasCompletedNotified, experimentId, router, toast]);

  const handleConfirmCancel = async () => {
    setIsCancelling(true);
    try {
      const ok = await cancelRun();
      if (ok) {
        toast({
          type: 'info',
          title: 'Experiment Cancelled',
          message: `Autopsy run ${experimentId} was terminated.`,
        });
        setIsCancelDialogOpen(false);
      }
    } finally {
      setIsCancelling(false);
    }
  };

  if (loading) {
    return (
      <AppShell showSidebar experimentId={experimentId}>
        <div className="max-w-6xl mx-auto w-full space-y-6">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-10 w-96" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Skeleton className="h-80 w-full rounded-xl" />
            <Skeleton className="h-80 w-full rounded-xl" />
          </div>
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell showSidebar experimentId={experimentId}>
        <ErrorState
          title="Experiment Error"
          message={error}
          onRetry={retryRun}
        />
      </AppShell>
    );
  }

  const isCancelled = experiment?.status === 'cancelled';
  const isFailed = experiment?.status === 'failed';
  const isCompleted = progressPercent >= 100 || experiment?.status === 'completed';

  return (
    <AppShell showSidebar experimentId={experimentId}>
      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-accent font-semibold px-2 py-0.5 rounded bg-accent/10 border border-accent/20">
                {experimentId}
              </span>
              <span className="text-xs text-text-subtle font-mono">
                {experiment?.taskType || 'classification'}
              </span>
            </div>
            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white tracking-tight">
              {isCancelled
                ? 'Autopsy Cancelled'
                : isFailed
                ? 'Autopsy Failed'
                : isCompleted
                ? 'Autopsy Complete'
                : 'Autopsy in Progress'}
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-0.5">
              Running stress tests on {experiment?.modelName || 'Random Forest'} ({experiment?.datasetName || 'Credit Risk Demo'})
            </p>
          </div>

          <div className="flex items-center gap-3">
            {isCompleted ? (
              <Link href={`/experiments/${experimentId}/results`}>
                <Button variant="primary" className="gap-2">
                  <span>View Results</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            ) : !isCancelled && !isFailed ? (
              <Button
                variant="destructive"
                onClick={() => setIsCancelDialogOpen(true)}
                className="gap-2"
              >
                <Ban className="w-4 h-4" />
                <span>Cancel</span>
              </Button>
            ) : (
              <Button variant="secondary" onClick={retryRun} className="gap-2">
                <RotateCw className="w-4 h-4" />
                <span>Retry Run</span>
              </Button>
            )}
          </div>
        </div>

        {/* Failed / Cancelled banner states */}
        {isCancelled && (
          <div className="p-4 rounded-xl bg-surface-2 border border-white/10 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 text-text-muted text-xs">
              <XCircle className="w-5 h-5 text-text-subtle" />
              <span>Experiment execution was manually aborted. Partial logs are retained for audit.</span>
            </div>
            <Button variant="secondary" size="sm" onClick={retryRun}>
              Restart Autopsy
            </Button>
          </div>
        )}

        {isFailed && (
          <div className="p-4 rounded-xl bg-accent/10 border border-accent/30 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 text-xs text-accent">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <span>
                {experiment?.errorMessage ||
                  'Loss diverged or runtime failure encountered during stress test.'}
              </span>
            </div>
            <Button variant="secondary" size="sm" onClick={retryRun}>
              Retry Execution
            </Button>
          </div>
        )}

        {/* Progress Grid: Left Circular Ring, Right Checklist */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
          <CircularProgressRing
            progress={progressPercent}
            caption={
              isCompleted
                ? 'Stress testing finished'
                : isCancelled
                ? 'Run cancelled'
                : isFailed
                ? 'Run failed'
                : 'Running stress tests…'
            }
          />
          <RunningChecklist
            currentStage={currentStage}
            completedStages={completedStages}
          />
        </div>

        {/* Bottom Telemetry & Performance Row */}
        <LiveTelemetry
          currentStage={currentStage}
          progressPercent={progressPercent}
          elapsedSeconds={elapsedSeconds}
          metric={experiment?.metric || 'f1'}
          baselineScore={0.958}
        />

        {/* Cancel Confirmation Dialog */}
        <Dialog
          open={isCancelDialogOpen}
          onClose={() => setIsCancelDialogOpen(false)}
          title="Abort Autopsy Execution?"
          description="Are you sure you want to cancel this stress test? Running processes will terminate and incomplete perturbation steps will be abandoned."
        >
          <div className="space-y-4 pt-2">
            <p className="text-xs text-text-muted leading-relaxed">
              Target endpoint contract note: calls <code>POST /experiments/{experimentId}/cancel</code>.
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setIsCancelDialogOpen(false)}
                disabled={isCancelling}
              >
                Continue Run
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleConfirmCancel}
                loading={isCancelling}
              >
                Abort Autopsy
              </Button>
            </div>
          </div>
        </Dialog>
      </div>
    </AppShell>
  );
}
