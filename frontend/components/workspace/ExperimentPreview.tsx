'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Database, Cpu, Activity, AlertOctagon, Hash } from 'lucide-react';
import { WorkspaceConfig } from '@/lib/yaml';
import { Badge } from '@/components/ui/Badge';

interface ExperimentPreviewProps {
  config: Partial<WorkspaceConfig>;
  step: number;
}

export function ExperimentPreview({ config, step }: ExperimentPreviewProps) {
  const fields = [
    {
      label: 'Dataset',
      value: config.datasetName,
      icon: Database,
      stepIndicator: 1,
    },
    {
      label: 'Model',
      value: config.modelName,
      icon: Cpu,
      stepIndicator: 2,
    },
    {
      label: 'Task Type',
      value: config.taskType
        ? config.taskType.charAt(0).toUpperCase() + config.taskType.slice(1)
        : undefined,
      icon: Sparkles,
      stepIndicator: 1,
    },
    {
      label: 'Stress Type',
      value: config.stressType
        ? config.stressType.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
        : undefined,
      icon: AlertOctagon,
      stepIndicator: 4,
    },
    {
      label: 'Severity Levels',
      value:
        config.severityLevels && config.severityLevels.length > 0
          ? config.severityLevels.map((s) => `${Math.round(s * 100)}%`).join(', ')
          : undefined,
      icon: Activity,
      stepIndicator: 4,
    },
    {
      label: 'Metric / Threshold',
      value:
        config.metric && config.failureThreshold !== undefined
          ? `${config.metric.toUpperCase()} @ ${config.failureThreshold}`
          : undefined,
      icon: Activity,
      stepIndicator: 4,
    },
    {
      label: 'Split & Seed',
      value:
        config.testSize !== undefined && config.seed !== undefined
          ? `${Math.round(config.testSize * 100)}% test · seed ${config.seed}`
          : undefined,
      icon: Hash,
      stepIndicator: 3,
    },
  ];

  return (
    <aside className="w-full lg:w-80 flex-shrink-0 sticky top-24 self-start">
      <div className="bg-surface rounded-xl border border-border p-5 shadow-xl relative overflow-hidden">
        {/* Subtle accent glow top-right */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 rounded-full blur-2xl pointer-events-none" />

        <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-accent" />
            <h3 className="font-manrope font-semibold text-sm text-white">
              Experiment Preview
            </h3>
          </div>
          <Badge variant="outline" className="text-[10px] text-text-subtle">
            Step {step} of 5
          </Badge>
        </div>

        <div className="space-y-3.5">
          {fields.map((f) => {
            const Icon = f.icon;
            const isAssigned = !!f.value;

            return (
              <div
                key={f.label}
                className="flex items-start justify-between gap-3 text-xs"
              >
                <div className="flex items-center gap-2 text-text-subtle font-cabin">
                  <Icon className="w-3.5 h-3.5 text-text-subtle/70" />
                  <span>{f.label}</span>
                </div>

                <div className="text-right max-w-[170px] truncate font-medium">
                  <AnimatePresence mode="wait">
                    {isAssigned ? (
                      <motion.span
                        key={String(f.value)}
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 4 }}
                        transition={{ duration: 0.2 }}
                        className="text-white font-manrope font-semibold"
                      >
                        {f.value}
                      </motion.span>
                    ) : (
                      <motion.span
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 0.4 }}
                        exit={{ opacity: 0 }}
                        className="text-text-subtle"
                      >
                        —
                      </motion.span>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            );
          })}
        </div>

        {/* Live validation summary status */}
        <div className="mt-6 pt-4 border-t border-white/5">
          <p className="text-[11px] text-text-subtle font-cabin leading-relaxed">
            Experiments are versioned and seeded for reproducible stress-testing.
          </p>
        </div>
      </div>
    </aside>
  );
}
