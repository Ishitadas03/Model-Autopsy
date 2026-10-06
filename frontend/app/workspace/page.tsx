'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, ArrowRight, AlertCircle } from 'lucide-react';

import { AppShell } from '@/components/layout/AppShell';
import { Stepper, WORKSPACE_STEPS } from '@/components/workspace/Stepper';
import { ExperimentPreview } from '@/components/workspace/ExperimentPreview';
import { Step1Dataset } from '@/components/workspace/Step1Dataset';
import { Step2Model } from '@/components/workspace/Step2Model';
import { Step3Baseline } from '@/components/workspace/Step3Baseline';
import { Step4StressTest } from '@/components/workspace/Step4StressTest';
import { Step5Review } from '@/components/workspace/Step5Review';

import { WorkspaceConfig } from '@/lib/yaml';
import { validateStep } from '@/lib/validators';
import { Dataset, ModelAdapter } from '@/lib/schemas';
import { Button } from '@/components/ui/Button';
import { Tooltip } from '@/components/ui/Tooltip';

const DRAFT_STORAGE_KEY = 'model_autopsy_workspace_draft';

const DEFAULT_CONFIG: WorkspaceConfig = {
  datasetId: 'credit-risk-demo',
  datasetName: 'Credit Risk Demo (synthetic)',
  taskType: 'classification',
  modelId: 'random-forest-classifier',
  modelName: 'Random Forest Classifier',
  modelParams: {
    n_estimators: 100,
    max_depth: 10,
    min_samples_split: 2,
  },
  testSize: 0.2,
  seed: 42,
  numSeeds: 1,
  stressType: 'gaussian_noise',
  severityLevels: [0.05, 0.1, 0.2, 0.3],
  stressMode: 'random',
  targetFeatures: [],
  metric: 'f1',
  failureThreshold: 0.8,
};

function WorkspaceContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Step resolution from URL ?step=
  const stepParam = searchParams?.get('step');
  const initialStep = stepParam
    ? WORKSPACE_STEPS.find((s) => s.slug === stepParam)?.id || 1
    : 1;

  const [currentStep, setCurrentStep] = useState<number>(initialStep);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [config, setConfig] = useState<WorkspaceConfig>(DEFAULT_CONFIG);
  const [baselineDone, setBaselineDone] = useState(false);

  // Load draft from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(DRAFT_STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setConfig((prev) => ({ ...prev, ...parsed }));
      }
    } catch (e) {
      console.warn('Could not restore workspace draft', e);
    }
  }, []);

  // Persist draft to localStorage on change
  useEffect(() => {
    try {
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(config));
    } catch (e) {
      // quota or private browsing
    }
  }, [config]);

  // Sync step changes to URL
  const handleStepChange = (stepId: number) => {
    setCurrentStep(stepId);
    const slug = WORKSPACE_STEPS.find((s) => s.id === stepId)?.slug || 'dataset';
    router.replace(`/workspace?step=${slug}`, { scroll: false });
  };

  // Validation gate for current step
  const stepValidation = validateStep(currentStep as any, config);
  const canProceed = stepValidation.isValid;

  const handleNext = () => {
    if (!canProceed) return;
    if (!completedSteps.includes(currentStep)) {
      setCompletedSteps((prev) => [...prev, currentStep]);
    }
    if (currentStep < 5) {
      handleStepChange(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      handleStepChange(currentStep - 1);
    }
  };

  const nextStepName =
    WORKSPACE_STEPS.find((s) => s.id === currentStep + 1)?.title || 'Next';

  return (
    <AppShell showSidebar>
      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Header with Title and Floating Brain Poster */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-white/5 relative">
          <div>
            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl lg:text-[34px] text-white tracking-tight">
              Autopsy Workspace
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-1 max-w-xl">
              Configure a new experiment to test your model&apos;s robustness under controlled stress.
            </p>
          </div>

          {/* Decorative small brain element with slow float animation */}
          <div className="relative w-16 h-16 sm:w-20 sm:h-20 flex-shrink-0 select-none">
            <motion.div
              animate={{ y: [-4, 4, -4], rotateZ: [-2, 2, -2] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
              className="w-full h-full relative"
            >
              <Image
                src="/assets/brain-isolated.png"
                alt="Model Autopsy Static Brain"
                fill
                sizes="80px"
                className="object-contain filter drop-shadow-[0_0_15px_rgba(239,68,68,0.35)]"
                priority
              />
            </motion.div>
          </div>
        </div>

        {/* 5-Step Stepper */}
        <Stepper
          currentStep={currentStep}
          onStepClick={handleStepChange}
          completedSteps={completedSteps}
        />

        {/* Workspace 2/3 Main Form + 1/3 Sticky Preview Panel */}
        <div className="flex flex-col lg:flex-row gap-6 items-start">
          {/* Main Card (2/3) */}
          <div className="flex-1 w-full bg-surface rounded-xl border border-border p-6 shadow-xl relative min-w-0">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25 }}
              >
                {currentStep === 1 && (
                  <Step1Dataset
                    selectedDatasetId={config.datasetId}
                    onSelectDataset={(d: Dataset) => {
                      setConfig((prev) => ({
                        ...prev,
                        datasetId: d.id,
                        datasetName: d.name,
                        taskType: d.taskType,
                        // Reset target features if dataset changes
                        targetFeatures: [],
                      }));
                    }}
                  />
                )}

                {currentStep === 2 && (
                  <Step2Model
                    taskType={config.taskType}
                    selectedModelId={config.modelId}
                    selectedModelParams={config.modelParams}
                    onSelectModel={(m: ModelAdapter) => {
                      setConfig((prev) => ({
                        ...prev,
                        modelId: m.id,
                        modelName: m.name,
                        modelParams: m.parameters,
                      }));
                    }}
                    onUpdateParams={(params) => {
                      setConfig((prev) => ({ ...prev, modelParams: params }));
                    }}
                  />
                )}

                {currentStep === 3 && (
                  <Step3Baseline
                    taskType={config.taskType}
                    testSize={config.testSize}
                    seed={config.seed}
                    onUpdateSplit={(testSize, seed) => {
                      setConfig((prev) => ({ ...prev, testSize, seed }));
                    }}
                    baselineCompleted={baselineDone}
                    onBaselineComplete={() => setBaselineDone(true)}
                  />
                )}

                {currentStep === 4 && (
                  <Step4StressTest
                    taskType={config.taskType}
                    stressType={config.stressType}
                    severityLevels={config.severityLevels}
                    stressMode={config.stressMode}
                    targetFeatures={config.targetFeatures || []}
                    metric={config.metric}
                    failureThreshold={config.failureThreshold}
                    onUpdateStress={(updates) => {
                      setConfig((prev) => ({ ...prev, ...updates }));
                    }}
                  />
                )}

                {currentStep === 5 && <Step5Review config={config} />}
              </motion.div>
            </AnimatePresence>

            {/* Stepper Navigation Footer */}
            {currentStep < 5 && (
              <div className="mt-8 pt-5 border-t border-white/5 flex items-center justify-between">
                <Button
                  variant="secondary"
                  onClick={handleBack}
                  disabled={currentStep === 1}
                  className="gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Back</span>
                </Button>

                {canProceed ? (
                  <Button variant="primary" onClick={handleNext} className="gap-2">
                    <span>Next: {nextStepName}</span>
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                ) : (
                  <Tooltip content={stepValidation.error || 'Complete current step to proceed'}>
                    <Button variant="primary" disabled className="gap-2 opacity-50 cursor-not-allowed">
                      <span>Next: {nextStepName}</span>
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                  </Tooltip>
                )}
              </div>
            )}
          </div>

          {/* Sticky Experiment Preview (1/3) */}
          <ExperimentPreview config={config} step={currentStep} />
        </div>
      </div>
    </AppShell>
  );
}

export default function WorkspacePage() {
  return (
    <Suspense
      fallback={
        <AppShell showSidebar>
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
          </div>
        </AppShell>
      }
    >
      <WorkspaceContent />
    </Suspense>
  );
}
