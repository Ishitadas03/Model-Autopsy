'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Cpu, ShieldCheck, AlertCircle, Play, Sliders, Info } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { api } from '@/lib/api';
import { ModelAdapter } from '@/lib/schemas';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Callout } from '@/components/ui/Callout';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';

export default function ModelDetailPage() {
  const params = useParams();
  const router = useRouter();
  const modelId = params?.id as string;

  const [model, setModel] = useState<ModelAdapter | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadModel = async () => {
      setLoading(true);
      try {
        const all = await api.getModels();
        const match = all.find((m) => m.id === modelId);
        setModel(match || null);
      } finally {
        setLoading(false);
      }
    };

    loadModel();
  }, [modelId]);

  if (loading) {
    return (
      <AppShell showSidebar>
        <div className="max-w-5xl mx-auto w-full space-y-6">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-12 w-80" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      </AppShell>
    );
  }

  if (!model) {
    return (
      <AppShell showSidebar>
        <ErrorState
          title="Model Adapter Not Found"
          message={`No model adapter found with identifier "${modelId}".`}
          onRetry={() => router.push('/models')}
        />
      </AppShell>
    );
  }

  return (
    <AppShell showSidebar>
      <div className="max-w-5xl mx-auto w-full space-y-6">
        {/* Back Link */}
        <Link
          href="/models"
          className="inline-flex items-center gap-2 text-xs font-cabin text-text-subtle hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Models</span>
        </Link>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-text-subtle">{model.id}</span>
              <Badge variant="outline" className="text-[10px] font-mono">
                {model.framework}
              </Badge>
              {model.taskTypes.map((t) => (
                <Badge
                  key={t}
                  variant={t === 'classification' ? 'info' : 'outline'}
                  className="text-[10px] uppercase font-cabin"
                >
                  {t}
                </Badge>
              ))}
            </div>

            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white">
              {model.name}
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-1 max-w-2xl">
              {model.description}
            </p>
          </div>

          <Button
            variant="primary"
            onClick={() => router.push(`/workspace?step=model`)}
            className="gap-2"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Use in Autopsy →</span>
          </Button>
        </div>

        {/* Fixed Mandated Callout */}
        <Callout type="info" title="Zero Model File Uploads">
          Model files cannot be uploaded. Only supported adapters are available. Model instances are trained and tested strictly inside reproducible sandbox boundaries.
        </Callout>

        {/* Probability Calibration Info */}
        <div className="p-4 rounded-xl bg-surface border border-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            {model.predictProba ? (
              <ShieldCheck className="w-5 h-5 text-success" />
            ) : (
              <AlertCircle className="w-5 h-5 text-warning" />
            )}
            <div>
              <div className="text-xs font-manrope font-semibold text-white">
                {model.predictProba
                  ? 'Posterior Probability Estimation Enabled'
                  : 'Decision Function Output (Uncalibrated)'}
              </div>
              <p className="text-[11px] text-text-subtle">
                {model.predictProba
                  ? 'Outputs calibrated multi-class posterior probability vectors (predict_proba).'
                  : 'Outputs raw margin distances without probabilistic calibration.'}
              </p>
            </div>
          </div>
        </div>

        {/* Hyperparameters Schema Table */}
        <div className="bg-surface rounded-xl border border-border overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-accent" />
              <h3 className="font-manrope font-semibold text-sm text-white">
                Default Hyperparameters & Configuration
              </h3>
            </div>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Parameter Key</TableHead>
                <TableHead>Default Value</TableHead>
                <TableHead>Type</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(model.parameters).map(([key, val]) => (
                <TableRow key={key}>
                  <TableCell className="font-mono text-xs font-medium text-white">
                    {key}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-text-muted">
                    {JSON.stringify(val)}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-text-subtle">
                    {typeof val}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </AppShell>
  );
}
