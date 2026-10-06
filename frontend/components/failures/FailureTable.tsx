'use client';

import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { XCircle, ChevronRight, ChevronLeft, AlertOctagon } from 'lucide-react';
import { FailedSample } from '@/lib/schemas';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

interface FailureTableProps {
  samples: FailedSample[];
  selectedSampleId?: string;
  onSelectSample: (sample: FailedSample) => void;
  currentPage: number;
  pageSize: number;
  totalSamples: number;
  onPageChange: (page: number) => void;
}

export function FailureTable({
  samples,
  selectedSampleId,
  onSelectSample,
  currentPage,
  pageSize,
  totalSamples,
  onPageChange,
}: FailureTableProps) {
  const tableRef = useRef<HTMLDivElement>(null);
  const totalPages = Math.max(1, Math.ceil(totalSamples / pageSize));

  // Keyboard navigation (ArrowUp, ArrowDown, Enter)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!samples.length) return;
      const currentIndex = samples.findIndex((s) => s.id === selectedSampleId);

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        const nextIndex = currentIndex < samples.length - 1 ? currentIndex + 1 : 0;
        onSelectSample(samples[nextIndex]);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : samples.length - 1;
        onSelectSample(samples[prevIndex]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [samples, selectedSampleId, onSelectSample]);

  return (
    <div ref={tableRef} className="bg-surface rounded-xl border border-border shadow-xl overflow-hidden flex flex-col justify-between">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-16"># Sample</TableHead>
              <TableHead>True Label</TableHead>
              <TableHead>Predicted (Misclassified)</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Stress Type</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead className="w-10"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {samples.map((sample, idx) => {
              const isSelected = selectedSampleId === sample.id;

              return (
                <TableRow
                  key={sample.id}
                  onClick={() => onSelectSample(sample)}
                  className={`cursor-pointer transition-colors relative ${
                    isSelected
                      ? 'bg-surface-2 border-l-2 border-white text-white'
                      : 'hover:bg-surface-2/60 text-text-muted hover:text-white'
                  }`}
                >
                  <TableCell className="font-mono text-xs text-text-subtle font-medium">
                    #{sample.sampleIndex}
                  </TableCell>

                  <TableCell className="font-mono text-xs text-white">
                    <Badge variant="outline" className="text-[10px]">
                      {String(sample.trueLabel)}
                    </Badge>
                  </TableCell>

                  {/* Predicted mismatch with mandatory Icon + Red Text (never color-only) */}
                  <TableCell>
                    <div className="flex items-center gap-1.5 text-accent font-mono text-xs font-semibold">
                      <XCircle className="w-3.5 h-3.5 stroke-[2.5] flex-shrink-0" />
                      <span>{String(sample.predictedLabel)}</span>
                    </div>
                  </TableCell>

                  <TableCell className="font-mono text-xs tabular-nums text-text-muted">
                    {(sample.confidence * 100).toFixed(1)}%
                  </TableCell>

                  <TableCell className="font-mono text-xs text-text-subtle">
                    {sample.stressType.replace('_', ' ')}
                  </TableCell>

                  <TableCell className="font-mono text-xs text-accent">
                    {Math.round(sample.severity * 100)}%
                  </TableCell>

                  <TableCell className="text-right">
                    <ChevronRight
                      className={`w-4 h-4 transition-transform ${
                        isSelected ? 'text-white translate-x-1' : 'text-text-subtle'
                      }`}
                    />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Footer */}
      <div className="p-4 border-t border-white/5 flex items-center justify-between text-xs font-manrope">
        <span className="text-text-subtle">
          Showing {(currentPage - 1) * pageSize + 1}–
          {Math.min(currentPage * pageSize, totalSamples)} of {totalSamples} failed instances
        </span>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className="p-1.5"
            aria-label="Previous page"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>

          <span className="font-mono text-text-subtle px-2">
            {currentPage} / {totalPages}
          </span>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="p-1.5"
            aria-label="Next page"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
