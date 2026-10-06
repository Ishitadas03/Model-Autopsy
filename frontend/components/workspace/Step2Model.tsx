'use client';

import React from 'react';
import { Check, Cpu, ShieldCheck, AlertCircle, Info, Sliders } from 'lucide-react';
import { ModelAdapter, TaskType } from '@/lib/schemas';
import { MOCK_MODELS } from '@/lib/mocks/models';
import { Badge } from '@/components/ui/Badge';
import { Callout } from '@/components/ui/Callout';

interface Step2ModelProps {
  taskType?: TaskType;
  selectedModelId?: string;
  selectedModelParams?: Record<string, any>;
  onSelectModel: (model: ModelAdapter) => void;
  onUpdateParams: (params: Record<string, any>) => void;
}

export function Step2Model({
  taskType = 'classification',
  selectedModelId,
  selectedModelParams = {},
  onSelectModel,
  onUpdateParams,
}: Step2ModelProps) {
  // Filter models compatible with current dataset task type
  const compatibleModels = MOCK_MODELS.filter((m) =>
    m.taskTypes.includes(taskType)
  );

  const selectedModel = MOCK_MODELS.find((m) => m.id === selectedModelId);

  const handleParamChange = (paramKey: string, val: any) => {
    onUpdateParams({
      ...selectedModelParams,
      [paramKey]: val,
    });
  };

  return (
    <div className="space-y-6">
      {/* Fixed Mandated Honesty Callout */}
      <Callout type="info" title="Adapter-Only Architecture">
        Model files cannot be uploaded. Only supported adapters are available. All selected
        models are trained and evaluated in isolated environments under identical split and perturbation seeds.
      </Callout>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {compatibleModels.map((model) => {
          const isSelected = selectedModelId === model.id;

          return (
            <div
              key={model.id}
              role="button"
              tabIndex={0}
              onClick={() => onSelectModel(model)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectModel(model);
                }
              }}
              className={`relative p-5 rounded-xl border transition-all text-left flex flex-col justify-between cursor-pointer group ${
                isSelected
                  ? 'bg-surface-2 border-white ring-2 ring-white/20 shadow-[0_0_24px_rgba(255,255,255,0.12)]'
                  : 'bg-surface border-border hover:border-border-strong hover:bg-surface/80'
              }`}
            >
              {isSelected && (
                <div className="absolute top-4 right-4 w-5 h-5 rounded-full bg-white text-black flex items-center justify-center shadow-lg">
                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                </div>
              )}

              <div>
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-8 h-8 rounded-lg bg-surface border border-white/10 flex items-center justify-center text-white">
                    <Cpu className="w-4 h-4 text-accent" />
                  </div>
                  <div>
                    <h4 className="font-manrope font-semibold text-sm text-white">
                      {model.name}
                    </h4>
                    <span className="text-[11px] font-mono text-text-subtle">
                      {model.framework}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-text-muted leading-relaxed line-clamp-2 mt-2">
                  {model.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                <Badge variant="outline" className="text-[10px] font-cabin">
                  {model.framework}
                </Badge>

                {model.predictProba ? (
                  <span className="text-[10px] font-cabin text-success flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" />
                    Probabilities calibrated
                  </span>
                ) : (
                  <span className="text-[10px] font-cabin text-warning flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Decision boundary / uncalibrated
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* SVM uncalibrated probability caveat */}
      {selectedModelId === 'svm-classifier' && (
        <div className="p-3.5 rounded-lg bg-warning/10 border border-warning/20 text-xs text-warning flex items-start gap-2">
          <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            <strong>SVC Calibration Notice:</strong> Support Vector Classifiers do not produce natively calibrated posterior probabilities without Platt scaling. Confidence scores represent raw distance to margin.
          </span>
        </div>
      )}

      {/* Hyperparameter Configuration Panel */}
      {selectedModel && (
        <div className="p-5 rounded-xl bg-surface border border-border space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-white/5">
            <Sliders className="w-4 h-4 text-text-subtle" />
            <h4 className="font-manrope font-semibold text-xs text-white uppercase tracking-wider">
              {selectedModel.name} Parameters
            </h4>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(selectedModel.parameters).map(([key, defaultVal]) => {
              const currentVal =
                selectedModelParams[key] !== undefined
                  ? selectedModelParams[key]
                  : defaultVal;

              const isNumber = typeof defaultVal === 'number';

              return (
                <div key={key} className="space-y-1.5">
                  <label className="block text-xs font-mono text-text-subtle">
                    {key}
                  </label>
                  <input
                    type={isNumber ? 'number' : 'text'}
                    value={currentVal}
                    step={isNumber && defaultVal < 1 ? '0.01' : '1'}
                    onChange={(e) =>
                      handleParamChange(
                        key,
                        isNumber ? parseFloat(e.target.value) || 0 : e.target.value
                      )
                    }
                    className="w-full bg-surface-2 border border-border rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-white/40"
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
