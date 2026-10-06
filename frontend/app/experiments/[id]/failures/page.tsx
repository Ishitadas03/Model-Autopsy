'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ShieldAlert, BarChart3, AlertOctagon, Download } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { api } from '@/lib/api';
import { FailedSample } from '@/lib/schemas';
import { MOCK_FAILED_SAMPLES } from '@/lib/mocks/experiments';
import { Callout } from '@/components/ui/Callout';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { FailureFilters } from '@/components/failures/FailureFilters';
import { FailureTable } from '@/components/failures/FailureTable';
import { SampleAnalysisCard } from '@/components/failures/SampleAnalysisCard';

function FailureExplorerContent() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const experimentId = (params?.id as string) || 'EXP-0241';

  // Filters state with URL parameter initialization
  const initialClass = searchParams?.get('class') || 'All';
  const initialSeverity = searchParams?.get('severity') || 'All';
  const initialQuery = searchParams?.get('q') || '';

  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [selectedClass, setSelectedClass] = useState(initialClass);
  const [selectedSeverity, setSelectedSeverity] = useState(initialSeverity);
  const [confidenceRange, setConfidenceRange] = useState<[number, number]>([0.5, 1.0]);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  const [samples, setSamples] = useState<FailedSample[]>([]);
  const [selectedSample, setSelectedSample] = useState<FailedSample | null>(null);
  const [loading, setLoading] = useState(true);

  // Sync state to URL search parameters
  const updateUrlParams = (cls: string, sev: string, q: string) => {
    const params = new URLSearchParams();
    if (cls !== 'All') params.set('class', cls);
    if (sev !== 'All') params.set('severity', sev);
    if (q.trim()) params.set('q', q);
    router.replace(`/experiments/${experimentId}/failures?${params.toString()}`, { scroll: false });
  };

  useEffect(() => {
    let isMounted = true;
    const loadSamples = async () => {
      setLoading(true);
      try {
        const res = await api.getFailedSamples(experimentId, 1, 200);
        if (isMounted) {
          setSamples(res.samples.length ? res.samples : MOCK_FAILED_SAMPLES);
          setSelectedSample(res.samples[0] || MOCK_FAILED_SAMPLES[0] || null);
        }
      } catch {
        if (isMounted) {
          setSamples(MOCK_FAILED_SAMPLES);
          setSelectedSample(MOCK_FAILED_SAMPLES[0] || null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadSamples();
    return () => {
      isMounted = false;
    };
  }, [experimentId]);

  // Filtered samples calculation
  const filteredSamples = samples.filter((s) => {
    if (selectedClass !== 'All' && s.trueLabel !== selectedClass) return false;
    if (selectedSeverity !== 'All' && s.severity !== parseFloat(selectedSeverity)) return false;
    if (s.confidence > confidenceRange[1]) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        s.id.toLowerCase().includes(q) ||
        String(s.sampleIndex).includes(q) ||
        String(s.trueLabel).toLowerCase().includes(q) ||
        String(s.predictedLabel).toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Current page slice
  const paginatedSamples = filteredSamples.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  // Export current filtered view to CSV
  const handleExportCsv = () => {
    const headers = ['ID', 'Sample #', 'True Label', 'Predicted', 'Confidence', 'Stress Type', 'Severity'];
    const rows = filteredSamples.map((s) => [
      s.id,
      s.sampleIndex,
      s.trueLabel,
      s.predictedLabel,
      s.confidence.toFixed(3),
      s.stressType,
      s.severity,
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `failures-${experimentId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Summary counts
  const fraudCount = samples.filter((s) => s.trueLabel === 'Fraud').length;
  const normalCount = samples.filter((s) => s.trueLabel === 'Normal').length;
  const noise30Count = samples.filter((s) => s.severity >= 0.3).length;

  return (
    <AppShell showSidebar={false}>
      <div className="max-w-7xl mx-auto w-full space-y-6">
        {/* Navigation & Header */}
        <div className="space-y-3">
          <Link
            href={`/experiments/${experimentId}/results`}
            className="inline-flex items-center gap-2 text-xs font-cabin text-text-subtle hover:text-white transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Results Dashboard</span>
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-xs text-accent font-semibold px-2 py-0.5 rounded bg-accent/10 border border-accent/20">
                  {experimentId}
                </span>
                <span className="text-xs text-text-subtle font-mono">143 Failed Samples</span>
              </div>
              <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white tracking-tight">
                Failure Explorer
              </h1>
              <p className="text-xs sm:text-sm text-text-muted mt-0.5">
                Inspect misclassified samples, perturbation drifts, and decision boundary collapses.
              </p>
            </div>
          </div>
        </div>

        {/* Mandated Privacy Callout */}
        <Callout type="honesty" title="Privacy Preservation Guardrail">
          Only sample identifiers and selected features are shown. Raw records are intentionally not displayed to protect underlying data privacy and proprietary schemas.
        </Callout>

        {/* Summary Strip Above Table */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-surface border border-border flex items-center justify-between">
            <span className="text-xs font-cabin uppercase text-text-subtle">
              Total Failures
            </span>
            <span className="font-manrope font-bold text-xl text-accent">
              {samples.length} instances
            </span>
          </div>

          <div className="p-4 rounded-xl bg-surface border border-border flex items-center justify-between">
            <span className="text-xs font-cabin uppercase text-text-subtle">
              Minority (Fraud) Drops
            </span>
            <div className="text-right">
              <span className="font-manrope font-bold text-xl text-white">
                {fraudCount}
              </span>
              <span className="text-[11px] text-text-subtle block">
                ({((fraudCount / samples.length) * 100).toFixed(1)}% of failures)
              </span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-surface border border-border flex items-center justify-between">
            <span className="text-xs font-cabin uppercase text-text-subtle">
              Severe Noise (&ge;30%)
            </span>
            <div className="text-right">
              <span className="font-manrope font-bold text-xl text-white">
                {noise30Count}
              </span>
              <span className="text-[11px] text-text-subtle block">
                ({((noise30Count / samples.length) * 100).toFixed(1)}% of failures)
              </span>
            </div>
          </div>
        </div>

        {/* Filters Bar */}
        <FailureFilters
          searchQuery={searchQuery}
          onSearchChange={(q) => {
            setSearchQuery(q);
            setCurrentPage(1);
            updateUrlParams(selectedClass, selectedSeverity, q);
          }}
          selectedClass={selectedClass}
          onClassChange={(cls) => {
            setSelectedClass(cls);
            setCurrentPage(1);
            updateUrlParams(cls, selectedSeverity, searchQuery);
          }}
          selectedSeverity={selectedSeverity}
          onSeverityChange={(sev) => {
            setSelectedSeverity(sev);
            setCurrentPage(1);
            updateUrlParams(selectedClass, sev, searchQuery);
          }}
          confidenceRange={confidenceRange}
          onConfidenceRangeChange={(range) => {
            setConfidenceRange(range);
            setCurrentPage(1);
          }}
          onExportCsv={handleExportCsv}
        />

        {/* Two-Column Grid: Left Failure Table, Right Sticky Sample Analysis */}
        {loading ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full rounded-lg" />
              ))}
            </div>
            <Skeleton className="h-96 w-full rounded-xl" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
            <div className="lg:col-span-2">
              <FailureTable
                samples={paginatedSamples}
                selectedSampleId={selectedSample?.id}
                onSelectSample={(s) => setSelectedSample(s)}
                currentPage={currentPage}
                pageSize={pageSize}
                totalSamples={filteredSamples.length}
                onPageChange={(p) => setCurrentPage(p)}
              />
            </div>

            <div className="lg:col-span-1">
              <SampleAnalysisCard sample={selectedSample} />
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}

export default function FailureExplorerPage() {
  return (
    <Suspense
      fallback={
        <AppShell showSidebar={false}>
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
          </div>
        </AppShell>
      }
    >
      <FailureExplorerContent />
    </Suspense>
  );
}
