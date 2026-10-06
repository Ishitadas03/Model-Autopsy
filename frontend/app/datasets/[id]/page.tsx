'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Database, Layers, BarChart3, Play, AlertCircle, ShieldCheck } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { api } from '@/lib/api';
import { Dataset } from '@/lib/schemas';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';

export default function DatasetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const datasetId = params?.id as string;

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDataset = async () => {
      setLoading(true);
      try {
        const all = await api.getDatasets();
        const match = all.find((d) => d.id === datasetId);
        setDataset(match || null);
      } finally {
        setLoading(false);
      }
    };

    loadDataset();
  }, [datasetId]);

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

  if (!dataset) {
    return (
      <AppShell showSidebar>
        <ErrorState
          title="Dataset Not Found"
          message={`No dataset found with identifier "${datasetId}".`}
          onRetry={() => router.push('/datasets')}
        />
      </AppShell>
    );
  }

  return (
    <AppShell showSidebar>
      <div className="max-w-5xl mx-auto w-full space-y-6">
        {/* Back Link */}
        <Link
          href="/datasets"
          className="inline-flex items-center gap-2 text-xs font-cabin text-text-subtle hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Datasets</span>
        </Link>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-text-subtle">{dataset.id}</span>
              <Badge
                variant={dataset.taskType === 'classification' ? 'info' : 'outline'}
                className="text-[10px] uppercase font-cabin"
              >
                {dataset.taskType}
              </Badge>
            </div>
            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white">
              {dataset.name}
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-1 max-w-2xl">
              {dataset.description}
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

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl bg-surface border border-border">
            <span className="text-[11px] font-cabin uppercase text-text-subtle">Samples</span>
            <div className="font-manrope text-xl font-bold text-white mt-1">
              {dataset.sampleCount.toLocaleString()}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-surface border border-border">
            <span className="text-[11px] font-cabin uppercase text-text-subtle">Features</span>
            <div className="font-manrope text-xl font-bold text-white mt-1">
              {dataset.featureCount}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-surface border border-border">
            <span className="text-[11px] font-cabin uppercase text-text-subtle">Classes</span>
            <div className="font-manrope text-xl font-bold text-white mt-1">
              {dataset.classCount || 'N/A (Continuous)'}
            </div>
          </div>
          <div className="p-4 rounded-xl bg-surface border border-border">
            <span className="text-[11px] font-cabin uppercase text-text-subtle">Integrity</span>
            <div className="font-manrope text-xl font-bold text-success mt-1 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>Validated</span>
            </div>
          </div>
        </div>

        {/* Schema Breakdown Table */}
        <div className="bg-surface rounded-xl border border-border overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-accent" />
              <h3 className="font-manrope font-semibold text-sm text-white">
                Feature Schema & Missingness Audit
              </h3>
            </div>
            <span className="text-xs font-mono text-text-subtle">
              {dataset.features.length} columns verified
            </span>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Feature Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Missing Count</TableHead>
                <TableHead>Completeness</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dataset.features.map((feature) => {
                const completeness =
                  ((dataset.sampleCount - feature.missingCount) / dataset.sampleCount) * 100;

                return (
                  <TableRow key={feature.name}>
                    <TableCell className="font-mono font-medium text-white">
                      {feature.name}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-[10px] font-mono">
                        {feature.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {feature.missingCount > 0 ? (
                        <span className="text-warning font-semibold">
                          {feature.missingCount}
                        </span>
                      ) : (
                        <span className="text-text-subtle">0</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 bg-surface-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              completeness < 100 ? 'bg-warning' : 'bg-success'
                            }`}
                            style={{ width: `${completeness}%` }}
                          />
                        </div>
                        <span className="font-mono text-xs text-text-subtle">
                          {completeness.toFixed(1)}%
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>
    </AppShell>
  );
}
