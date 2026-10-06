'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Copy, Check, Play, Save, FileCode, CheckCircle2, ShieldAlert } from 'lucide-react';
import { WorkspaceConfig, generateExperimentYaml, generateManifestJson } from '@/lib/yaml';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Tabs } from '@/components/ui/Tabs';
import { Badge } from '@/components/ui/Badge';
import { useToast } from '@/components/ui/Toast';

interface Step5ReviewProps {
  config: WorkspaceConfig;
}

export function Step5Review({ config }: Step5ReviewProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<'yaml' | 'manifest'>('yaml');
  const [isCopied, setIsCopied] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const yamlContent = generateExperimentYaml(config);
  const manifestContent = generateManifestJson(config);

  const handleCopy = async () => {
    const textToCopy = activeTab === 'yaml' ? yamlContent : manifestContent;
    try {
      await navigator.clipboard.writeText(textToCopy);
      setIsCopied(true);
      toast({
        type: 'success',
        title: 'Copied to clipboard',
        message: `Experiment ${activeTab.toUpperCase()} specification copied.`,
      });
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      toast({
        type: 'error',
        title: 'Copy failed',
        message: 'Could not access clipboard.',
      });
    }
  };

  const handleSaveDraft = async () => {
    setIsSubmitting(true);
    try {
      const exp = await api.createExperiment({
        title: `${config.modelName || 'Model'} Autopsy Draft`,
        datasetId: config.datasetId || 'credit-risk-demo',
        datasetName: config.datasetName || 'Credit Risk Demo',
        modelId: config.modelId || 'random-forest-classifier',
        modelName: config.modelName || 'Random Forest',
        taskType: config.taskType || 'classification',
        stressConfig: {
          type: config.stressType as any,
          severityLevels: config.severityLevels,
          mode: config.stressMode,
          targetFeatures: config.targetFeatures,
        },
        metric: config.metric as any,
        failureThreshold: config.failureThreshold,
        testSize: config.testSize,
        seed: config.seed,
        numSeeds: config.numSeeds,
      });

      toast({
        type: 'info',
        title: 'Draft Saved',
        message: `Draft created as ${exp.id}`,
      });
      router.push('/experiments');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunAutopsy = async () => {
    setIsSubmitting(true);
    try {
      const exp = await api.createExperiment({
        title: `${config.modelName || 'Model'} Stress Test — ${config.datasetName || 'Dataset'}`,
        datasetId: config.datasetId || 'credit-risk-demo',
        datasetName: config.datasetName || 'Credit Risk Demo',
        modelId: config.modelId || 'random-forest-classifier',
        modelName: config.modelName || 'Random Forest',
        taskType: config.taskType || 'classification',
        stressConfig: {
          type: config.stressType as any,
          severityLevels: config.severityLevels,
          mode: config.stressMode,
          targetFeatures: config.targetFeatures,
        },
        metric: config.metric as any,
        failureThreshold: config.failureThreshold,
        testSize: config.testSize,
        seed: config.seed,
        numSeeds: config.numSeeds,
      });

      toast({
        type: 'success',
        title: 'Autopsy Queued',
        message: `Executing experiment ${exp.id}...`,
      });

      // Clear draft in localStorage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('model_autopsy_workspace_draft');
      }

      router.push(`/experiments/${exp.id}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Review summary cards */}
      <div className="p-5 rounded-xl bg-surface border border-border space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-white/5">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-success" />
            <h4 className="font-manrope font-semibold text-sm text-white">
              Experiment Specification Summary
            </h4>
          </div>
          <Badge variant="outline" className="text-xs font-mono">
            spec v1.0
          </Badge>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-manrope">
          <div>
            <span className="text-text-subtle font-cabin uppercase text-[10px] block">Dataset</span>
            <span className="font-semibold text-white mt-0.5 block">{config.datasetName}</span>
          </div>
          <div>
            <span className="text-text-subtle font-cabin uppercase text-[10px] block">Model Adapter</span>
            <span className="font-semibold text-white mt-0.5 block">{config.modelName}</span>
          </div>
          <div>
            <span className="text-text-subtle font-cabin uppercase text-[10px] block">Perturbation Type</span>
            <span className="font-semibold text-white mt-0.5 block">
              {config.stressType.replace('_', ' ')}
            </span>
          </div>
          <div>
            <span className="text-text-subtle font-cabin uppercase text-[10px] block">Metric Threshold</span>
            <span className="font-semibold text-white mt-0.5 block">
              {config.metric.toUpperCase()} @ {config.failureThreshold}
            </span>
          </div>
        </div>
      </div>

      {/* Code / YAML Specification Box */}
      <div className="p-5 rounded-xl bg-surface border border-border space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <Tabs
            tabs={[
              { id: 'yaml', label: 'Specification YAML' },
              { id: 'manifest', label: 'Manifest JSON' },
            ]}
            activeId={activeTab}
            onChange={(t) => setActiveTab(t as any)}
          />

          <Button variant="secondary" size="sm" onClick={handleCopy} className="gap-1.5">
            {isCopied ? (
              <>
                <Check className="w-3.5 h-3.5 text-success" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy {activeTab.toUpperCase()}</span>
              </>
            )}
          </Button>
        </div>

        <pre className="p-4 rounded-lg bg-surface-2 border border-border overflow-x-auto text-xs font-mono text-white/90 leading-relaxed max-h-72 scrollbar-thin">
          <code>{activeTab === 'yaml' ? yamlContent : manifestContent}</code>
        </pre>
      </div>

      {/* Execution Actions */}
      <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
        <Button
          variant="secondary"
          onClick={handleSaveDraft}
          disabled={isSubmitting}
          className="w-full sm:w-auto gap-2"
        >
          <Save className="w-4 h-4" />
          <span>Save as Draft</span>
        </Button>

        <Button
          variant="primary"
          onClick={handleRunAutopsy}
          loading={isSubmitting}
          className="w-full sm:w-auto px-8 gap-2 bg-white text-black hover:bg-neutral-200"
        >
          <Play className="w-4 h-4 fill-current" />
          <span>Run Autopsy →</span>
        </Button>
      </div>
    </div>
  );
}
