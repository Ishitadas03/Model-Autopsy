'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Database, Search, Layers, BarChart3, AlertTriangle, ArrowRight, Plus } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { api } from '@/lib/api';
import { Dataset } from '@/lib/schemas';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [taskFilter, setTaskFilter] = useState('all');

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    setLoading(true);
    try {
      const data = await api.getDatasets();
      setDatasets(data);
    } finally {
      setLoading(false);
    }
  };

  const filtered = datasets.filter((d) => {
    if (taskFilter !== 'all' && d.taskType !== taskFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        d.name.toLowerCase().includes(q) ||
        d.description.toLowerCase().includes(q) ||
        d.id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <AppShell showSidebar>
      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div>
            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white tracking-tight">
              Datasets
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-1">
              Curated benchmark and custom datasets for systematic stress-testing.
            </p>
          </div>

          <Link href="/workspace?step=dataset">
            <Button variant="primary" className="gap-2">
              <Plus className="w-4 h-4" />
              <span>Add / Upload Dataset</span>
            </Button>
          </Link>
        </div>

        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between bg-surface p-3.5 rounded-xl border border-border">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 text-text-subtle absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search datasets..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-surface-2 border border-border text-xs text-white placeholder-text-subtle focus:outline-none focus:border-white/40"
            />
          </div>

          <div className="flex items-center gap-3">
            <select
              value={taskFilter}
              onChange={(e) => setTaskFilter(e.target.value)}
              className="bg-surface-2 border border-border rounded-lg px-3 py-1.5 text-xs text-white font-cabin focus:outline-none"
            >
              <option value="all">All Task Types</option>
              <option value="classification">Classification</option>
              <option value="regression">Regression</option>
            </select>
          </div>
        </div>

        {/* Dataset Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="p-6 rounded-xl bg-surface border border-border space-y-4">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-4 w-32" />
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No datasets found"
            description="No datasets matched your current search filters."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filtered.map((dataset) => {
              const totalMissing = dataset.features.reduce((acc, f) => acc + (f.missingCount || 0), 0);

              return (
                <div
                  key={dataset.id}
                  className="p-6 rounded-xl bg-surface border border-border hover:border-border-strong transition-all flex flex-col justify-between group"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-manrope font-semibold text-base text-white group-hover:text-accent transition-colors">
                          {dataset.name}
                        </h3>
                        <span className="font-mono text-xs text-text-subtle">{dataset.id}</span>
                      </div>
                      <Badge
                        variant={dataset.taskType === 'classification' ? 'info' : 'outline'}
                        className="text-xs uppercase font-cabin"
                      >
                        {dataset.taskType}
                      </Badge>
                    </div>

                    <p className="text-xs text-text-muted leading-relaxed line-clamp-2">
                      {dataset.description}
                    </p>

                    {totalMissing > 0 && (
                      <div className="flex items-center gap-1.5 text-xs text-warning">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>{totalMissing} missing values across features</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-4 text-xs font-manrope text-text-subtle">
                      <span className="flex items-center gap-1.5">
                        <Database className="w-3.5 h-3.5" />
                        {dataset.sampleCount.toLocaleString()} samples
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5" />
                        {dataset.featureCount} features
                      </span>
                      {dataset.classCount && (
                        <span className="flex items-center gap-1.5">
                          <BarChart3 className="w-3.5 h-3.5" />
                          {dataset.classCount} classes
                        </span>
                      )}
                    </div>

                    <Link href={`/datasets/${dataset.id}`}>
                      <Button variant="secondary" size="sm" className="gap-1.5 text-xs">
                        <span>Schema</span>
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
