'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

export interface StepItem {
  id: number;
  slug: 'dataset' | 'model' | 'baseline' | 'stress' | 'review';
  number: string;
  title: string;
}

export const WORKSPACE_STEPS: StepItem[] = [
  { id: 1, slug: 'dataset', number: '01', title: 'Dataset' },
  { id: 2, slug: 'model', number: '02', title: 'Model' },
  { id: 3, slug: 'baseline', number: '03', title: 'Baseline' },
  { id: 4, slug: 'stress', number: '04', title: 'Stress Test' },
  { id: 5, slug: 'review', number: '05', title: 'Review' },
];

interface StepperProps {
  currentStep: number;
  onStepClick: (step: number) => void;
  completedSteps: number[];
}

export function Stepper({ currentStep, onStepClick, completedSteps }: StepperProps) {
  return (
    <div className="w-full py-4 mb-6">
      <div className="flex items-center justify-between max-w-4xl mx-auto px-4 relative">
        {WORKSPACE_STEPS.map((step, index) => {
          const isCompleted = completedSteps.includes(step.id);
          const isActive = currentStep === step.id;
          const isClickable = isCompleted || step.id <= Math.max(...completedSteps, 1);

          return (
            <React.Fragment key={step.id}>
              {/* Step indicator node */}
              <div className="flex flex-col items-center relative z-10">
                <button
                  type="button"
                  onClick={() => isClickable && onStepClick(step.id)}
                  disabled={!isClickable}
                  aria-current={isActive ? 'step' : undefined}
                  className={`w-11 h-11 rounded-full flex items-center justify-center font-manrope font-semibold text-xs transition-all duration-300 ${
                    isActive
                      ? 'bg-white text-black ring-4 ring-white/20 shadow-[0_0_20px_rgba(255,255,255,0.4)] scale-105'
                      : isCompleted
                      ? 'bg-surface-2 border border-white/40 text-white hover:border-white cursor-pointer'
                      : 'bg-surface border border-border text-text-subtle cursor-not-allowed opacity-60'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5 text-white stroke-[2.5]" />
                  ) : (
                    <span>{step.number}</span>
                  )}
                </button>

                <span
                  className={`mt-2 text-xs font-cabin uppercase tracking-wider transition-colors ${
                    isActive
                      ? 'text-white font-semibold'
                      : isCompleted
                      ? 'text-text-muted'
                      : 'text-text-subtle'
                  }`}
                >
                  {step.title}
                </span>
              </div>

              {/* Progress connector line */}
              {index < WORKSPACE_STEPS.length - 1 && (
                <div className="flex-1 mx-3 h-[2px] bg-border relative -top-3 overflow-hidden rounded">
                  <motion.div
                    className="absolute inset-y-0 left-0 bg-white"
                    initial={false}
                    animate={{
                      scaleX: completedSteps.includes(step.id) || currentStep > step.id ? 1 : 0,
                    }}
                    transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
                    style={{ transformOrigin: 'left' }}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
