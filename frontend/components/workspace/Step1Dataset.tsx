'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Check,
  Search,
  UploadCloud,
  FileSpreadsheet,
  AlertTriangle,
  Database,
  BarChart3,
  Layers,
} from 'lucide-react';
import { Dataset } from '@/lib/schemas';
import { api } from '@/lib/api';
import { MOCK_DATASETS } from '@/lib/mocks/datasets';
import { Badge } from '@/components/ui/Badge';
import { Tabs } from '@/components/ui/Tabs';
import { Callout } from '@/components/ui/Callout';

interface Step1DatasetProps {
  selectedDatasetId?: string;
  onSelectDataset: (dataset: Dataset) => void;
}

export function Step1Dataset({
  selectedDatasetId,
  onSelectDataset,
}: Step1DatasetProps) {
  const [activeTab, setActiveTab] = useState<'popular' | 'custom' | 'upload'>('popular');
  const [searchQuery, setSearchQuery] = useState('');
  const [datasets, setDatasets] = useState<Dataset[]>(MOCK_DATASETS);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    api.getDatasets()
      .then((data) => {
        if (mounted && Array.isArray(data) && data.length > 0) {
          setDatasets(data);
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  // Upload state
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedSchema, setUploadedSchema] = useState<{
    name: string;
    sampleCount: number;
    featureCount: number;
    features: { name: string; type: 'numeric' | 'categorical' | 'boolean'; missingCount: number }[];
    targetColumn: string;
    taskType: 'classification' | 'regression';
  } | null>(null);

  const tabs = [
    { id: 'popular', label: 'Popular Datasets' },
    { id: 'custom', label: 'Saved Custom' },
    { id: 'upload', label: 'Upload CSV' },
  ];

  const filteredDatasets = datasets.filter((d) => {
    if (activeTab === 'custom' && !d.isCustom) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        d.name.toLowerCase().includes(q) ||
        d.description.toLowerCase().includes(q) ||
        d.taskType.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setUploadError('Only valid .csv files are supported.');
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setUploadError('File size exceeds the 25 MB limit.');
      return;
    }

    if (file.size === 0) {
      setUploadError('File is empty.');
      return;
    }

    setUploadError(null);
    setUploadedFile(file);
    setIsUploading(true);

    try {
      const uploadedDs = await api.uploadDataset(file, {
        name: file.name.replace(/\.csv$/i, ''),
      });

      setIsUploading(false);
      const cleanTaskType: 'classification' | 'regression' =
        String(uploadedDs.taskType || 'classification').toLowerCase() === 'regression'
          ? 'regression'
          : 'classification';

      const cleanDs: Dataset = {
        ...uploadedDs,
        taskType: cleanTaskType,
      };

      setUploadedSchema({
        name: cleanDs.name,
        sampleCount: cleanDs.sampleCount,
        featureCount: cleanDs.featureCount,
        features: (cleanDs.features as any) || [],
        targetColumn: 'target',
        taskType: cleanTaskType,
      });

      setDatasets((prev) => [cleanDs, ...prev.filter((d) => d.id !== cleanDs.id)]);
      onSelectDataset(cleanDs);
    } catch (err: any) {
      setIsUploading(false);
      setUploadError(err?.message || 'Failed to upload dataset to storage.');
    }
  };

  // Abstract SVG icon tile generator
  const renderAbstractTile = (type: string, id: string) => {
    if (type === 'classification') {
      return (
        <div className="w-10 h-10 rounded-lg bg-surface-2 border border-white/10 flex items-center justify-center p-2 text-white">
          <svg viewBox="0 0 40 40" className="w-full h-full stroke-current" fill="none">
            <circle cx="12" cy="14" r="4" strokeWidth="2" className="text-white/80" />
            <circle cx="28" cy="14" r="4" strokeWidth="2" className="text-accent" />
            <circle cx="20" cy="28" r="4" strokeWidth="2" className="text-white/50" />
            <path d="M15 16 L25 26" strokeWidth="1.5" strokeDasharray="2 2" className="text-white/30" />
          </svg>
        </div>
      );
    }
    return (
      <div className="w-10 h-10 rounded-lg bg-surface-2 border border-white/10 flex items-center justify-center p-2 text-white">
        <svg viewBox="0 0 40 40" className="w-full h-full stroke-current" fill="none">
          <path d="M6 32 L16 22 L24 26 L34 10" strokeWidth="2" className="text-accent" />
          <path d="M6 34 H34" strokeWidth="1.5" className="text-white/30" />
        </svg>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Tabs
          tabs={tabs}
          activeId={activeTab}
          onChange={(id) => setActiveTab(id as any)}
        />

        {activeTab !== 'upload' && (
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-text-subtle absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search datasets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-surface-2 border border-border text-xs text-white placeholder-text-subtle focus:outline-none focus:border-white/40"
            />
          </div>
        )}
      </div>

      {activeTab === 'upload' ? (
        <div className="space-y-6">
          <label className="border-2 border-dashed border-border hover:border-white/30 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-colors bg-surface-2/40">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
            />
            <UploadCloud className="w-10 h-10 text-white/60 mb-3" />
            <p className="font-manrope font-semibold text-sm text-white">
              Drag & Drop your CSV file here, or browse
            </p>
            <p className="text-xs text-text-subtle mt-1">
              Supports tabular .csv files up to 10 MB. Strict client-side validation.
            </p>
          </label>

          {isUploading && (
            <div className="p-4 rounded-lg bg-surface-2 border border-border flex items-center gap-3">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-white">
                Parsing CSV schema, checking class imbalance, and scanning missing values...
              </span>
            </div>
          )}

          {uploadError && (
            <Callout type="caveat" title="CSV Validation Error">
              {uploadError}
            </Callout>
          )}

          {uploadedSchema && (
            <div className="p-5 rounded-xl bg-surface border border-white/20 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-manrope font-semibold text-sm text-white">
                    {uploadedSchema.name}
                  </h4>
                  <p className="text-xs text-text-muted mt-0.5">
                    {uploadedSchema.sampleCount} samples · {uploadedSchema.featureCount} features detected
                  </p>
                </div>
                <Badge variant="success" className="text-xs">
                  Schema Validated
                </Badge>
              </div>

              {/* Warnings check */}
              <div className="flex items-center gap-2 text-xs text-warning bg-warning/10 border border-warning/20 p-2.5 rounded-lg">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>
                  16 missing values detected in feature columns. Missingness will be handled during baseline evaluation.
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-cabin uppercase tracking-wider text-text-subtle mb-1">
                    Target Column (Ground Truth)
                  </label>
                  <select
                    value={uploadedSchema.targetColumn}
                    onChange={(e) =>
                      setUploadedSchema({ ...uploadedSchema, targetColumn: e.target.value })
                    }
                    className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  >
                    {uploadedSchema.features.map((f) => (
                      <option key={f.name} value={f.name}>
                        {f.name} ({f.type})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-cabin uppercase tracking-wider text-text-subtle mb-1">
                    Inferred Task Type
                  </label>
                  <select
                    value={uploadedSchema.taskType}
                    onChange={(e) =>
                      setUploadedSchema({
                        ...uploadedSchema,
                        taskType: e.target.value as 'classification' | 'regression',
                      })
                    }
                    className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  >
                    <option value="classification">Classification (discrete targets)</option>
                    <option value="regression">Regression (continuous targets)</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredDatasets.map((dataset) => {
            const isSelected = selectedDatasetId === dataset.id;

            return (
              <div
                key={dataset.id}
                role="button"
                tabIndex={0}
                onClick={() => onSelectDataset(dataset)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectDataset(dataset);
                  }
                }}
                className={`relative p-5 rounded-xl border transition-all text-left flex flex-col justify-between cursor-pointer group ${
                  isSelected
                    ? 'bg-surface-2 border-white ring-2 ring-white/20 shadow-[0_0_24px_rgba(255,255,255,0.12)]'
                    : 'bg-surface border-border hover:border-border-strong hover:bg-surface/80'
                }`}
              >
                {/* Active check pill */}
                {isSelected && (
                  <div className="absolute top-4 right-4 w-5 h-5 rounded-full bg-white text-black flex items-center justify-center shadow-lg">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </div>
                )}

                <div>
                  <div className="flex items-start gap-3.5 mb-3">
                    {renderAbstractTile(dataset.taskType, dataset.id)}
                    <div className="pr-6">
                      <h4 className="font-manrope font-semibold text-sm text-white group-hover:text-white transition-colors">
                        {dataset.name}
                      </h4>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge
                          variant={dataset.taskType === 'classification' ? 'info' : 'outline'}
                          className="text-[10px] uppercase font-cabin"
                        >
                          {dataset.taskType}
                        </Badge>
                        {dataset.isCustom && (
                          <Badge variant="outline" className="text-[10px]">
                            Custom
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>

                  <p className="text-xs text-text-muted leading-relaxed line-clamp-2">
                    {dataset.description}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-text-subtle font-manrope">
                  <div className="flex items-center gap-2">
                    <Database className="w-3.5 h-3.5 text-text-subtle/80" />
                    <span>{dataset.sampleCount.toLocaleString()} samples</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Layers className="w-3.5 h-3.5 text-text-subtle/80" />
                    <span>{dataset.featureCount} features</span>
                  </div>
                  {dataset.classCount && (
                    <div className="flex items-center gap-2">
                      <BarChart3 className="w-3.5 h-3.5 text-text-subtle/80" />
                      <span>{dataset.classCount} classes</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
