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
    <div className="w-full py-4 mb-8">
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
                  className={`w-11 h-11 rounded-full flex items-center justify-center font-mono font-bold text-xs transition-all duration-300 ${
                    isActive
                      ? 'bg-white text-black ring-4 ring-sky-400/30 shadow-[0_0_24px_rgba(56,189,248,0.5)] scale-110'
                      : isCompleted
                      ? 'bg-[#0a0c16] border border-sky-400/60 text-sky-400 shadow-[0_0_12px_rgba(56,189,248,0.25)] hover:border-sky-300 cursor-pointer'
                      : 'bg-[#0a0c16]/60 border border-white/10 text-white/30 cursor-not-allowed opacity-60'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-5 h-5 text-sky-400 stroke-[2.5]" />
                  ) : (
                    <span>{step.number}</span>
                  )}
                </button>

                <span
                  className={`mt-2.5 text-xs font-mono uppercase tracking-wider transition-colors ${
                    isActive
                      ? 'text-white font-bold drop-shadow-[0_0_8px_rgba(255,255,255,0.4)]'
                      : isCompleted
                      ? 'text-sky-400/90 font-medium'
                      : 'text-white/40'
                  }`}
                >
                  {step.title}
                </span>
              </div>

              {/* Progress connector line */}
              {index < WORKSPACE_STEPS.length - 1 && (
                <div className="flex-1 mx-3 h-[2px] bg-white/10 relative -top-3 overflow-hidden rounded">
                  <motion.div
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-sky-400 to-blue-500 shadow-[0_0_8px_#38bdf8]"
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
