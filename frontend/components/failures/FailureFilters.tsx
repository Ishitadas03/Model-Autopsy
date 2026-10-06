'use client';

import React, { useState } from 'react';
import { Search, SlidersHorizontal, Download, Filter } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface FailureFiltersProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedClass: string;
  onClassChange: (cls: string) => void;
  selectedSeverity: string;
  onSeverityChange: (sev: string) => void;
  confidenceRange: [number, number];
  onConfidenceRangeChange: (range: [number, number]) => void;
  onExportCsv: () => void;
}

export function FailureFilters({
  searchQuery,
  onSearchChange,
  selectedClass,
  onClassChange,
  selectedSeverity,
  onSeverityChange,
  confidenceRange,
  onConfidenceRangeChange,
  onExportCsv,
}: FailureFiltersProps) {
  const [showMoreFilters, setShowMoreFilters] = useState(false);

  return (
    <div className="bg-surface rounded-xl border border-border p-4 shadow-xl space-y-4">
      <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        {/* Search input */}
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-text-subtle absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search samples by ID, feature..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-surface-2 border border-border text-xs text-white placeholder-text-subtle focus:outline-none focus:border-white/40"
          />
        </div>

        {/* Primary Filter controls */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <div className="flex items-center gap-1.5 text-xs text-text-subtle font-cabin">
            <Filter className="w-3.5 h-3.5" />
            <span>Filter by:</span>
          </div>

          <select
            value={selectedClass}
            onChange={(e) => onClassChange(e.target.value)}
            className="bg-surface-2 border border-border rounded-lg px-3 py-1.5 text-xs text-white font-cabin focus:outline-none"
          >
            <option value="All">All Classes</option>
            <option value="Fraud">Fraud (Minority)</option>
            <option value="Normal">Normal</option>
          </select>

          <select
            value={selectedSeverity}
            onChange={(e) => onSeverityChange(e.target.value)}
            className="bg-surface-2 border border-border rounded-lg px-3 py-1.5 text-xs text-white font-cabin focus:outline-none"
          >
            <option value="All">All Severities</option>
            <option value="0.05">5% Noise</option>
            <option value="0.1">10% Noise</option>
            <option value="0.2">20% Noise</option>
            <option value="0.3">30% Noise</option>
          </select>

          <Button
            variant={showMoreFilters ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setShowMoreFilters(!showMoreFilters)}
            className="text-xs gap-1.5"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>More Filters</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={onExportCsv}
            className="text-xs gap-1.5"
            title="Export filtered failed samples to CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </Button>
        </div>
      </div>

      {/* Collapsible More Filters Panel */}
      {showMoreFilters && (
        <div className="pt-3 border-t border-white/5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-text-subtle">
              <span>Confidence Threshold Range</span>
              <span className="font-mono text-white">
                {confidenceRange[0].toFixed(2)} – {confidenceRange[1].toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="1.0"
              step="0.05"
              value={confidenceRange[1]}
              onChange={(e) =>
                onConfidenceRangeChange([confidenceRange[0], parseFloat(e.target.value)])
              }
              className="w-full accent-accent bg-surface-2 rounded-lg cursor-pointer"
            />
          </div>

          <div className="space-y-1 text-text-subtle">
            <span>Noise Perturbation Family</span>
            <div className="p-2 rounded bg-surface-2 border border-border font-mono text-white text-[11px]">
              Gaussian Perturbation (Normal Distribution)
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
