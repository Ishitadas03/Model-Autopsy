'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Loader2, Circle, ListOrdered } from 'lucide-react';
import { STAGES } from '@/hooks/useRunStatus';
import { Badge } from '@/components/ui/Badge';

interface RunningChecklistProps {
  currentStage: string;
  completedStages: string[];
}

export function RunningChecklist({
  currentStage,
  completedStages,
}: RunningChecklistProps) {
  return (
    <div className="bg-surface rounded-xl border border-border p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <ListOrdered className="w-4 h-4 text-accent" />
          <h3 className="font-manrope font-semibold text-sm text-white">
            Execution Stages
          </h3>
        </div>
        <span className="text-xs font-mono text-text-subtle">
          {completedStages.length}/{STAGES.length} Done
        </span>
      </div>

      <div className="space-y-3">
        {STAGES.map((stage, idx) => {
          const isCompleted = completedStages.includes(stage);
          const isRunning = currentStage === stage && !isCompleted;
          const isPending = !isCompleted && !isRunning;

          return (
            <motion.div
              key={stage}
              layout
              className={`flex items-center justify-between p-3.5 rounded-lg border transition-all ${
                isRunning
                  ? 'bg-accent/10 border-accent/40 shadow-[0_0_15px_rgba(239,68,68,0.15)]'
                  : isCompleted
                  ? 'bg-surface-2 border-white/10'
                  : 'bg-surface/50 border-white/5 opacity-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-[11px] text-text-subtle w-4">
                  0{idx + 1}
                </span>
                <span
                  className={`text-xs font-manrope font-medium ${
                    isRunning ? 'text-white font-semibold' : 'text-text-muted'
                  }`}
                >
                  {stage}
                </span>
              </div>

              {/* Status Indicator (Icon + Text, never color-only) */}
              <AnimatePresence mode="wait">
                {isCompleted && (
                  <motion.div
                    key="done"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-1.5 text-success text-xs font-cabin"
                  >
                    <div className="w-4 h-4 rounded-full bg-success/20 flex items-center justify-center">
                      <Check className="w-2.5 h-2.5 stroke-[3]" />
                    </div>
                    <span>Done</span>
                  </motion.div>
                )}

                {isRunning && (
                  <motion.div
                    key="running"
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-1.5 text-accent text-xs font-cabin font-medium"
                  >
                    <span className="w-2 h-2 rounded-full bg-accent animate-ping" />
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Running</span>
                  </motion.div>
                )}

                {isPending && (
                  <motion.div
                    key="pending"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex items-center gap-1.5 text-text-subtle text-xs font-cabin"
                  >
                    <Circle className="w-3.5 h-3.5 stroke-[1.5]" />
                    <span>Pending</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
