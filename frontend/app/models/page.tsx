'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Cpu, Search, Plus, ShieldCheck, AlertCircle, ArrowRight, Sliders, Check } from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { api } from '@/lib/api';
import { ModelAdapter } from '@/lib/schemas';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Callout } from '@/components/ui/Callout';
import { Dialog } from '@/components/ui/Dialog';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { useToast } from '@/components/ui/Toast';

export default function ModelsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [models, setModels] = useState<ModelAdapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [taskFilter, setTaskFilter] = useState('all');

  // Register Adapter dialog state
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [regName, setRegName] = useState('');
  const [regId, setRegId] = useState('');
  const [regTask, setRegTask] = useState<'classification' | 'regression'>('classification');
  const [regDesc, setRegDesc] = useState('');

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    setLoading(true);
    try {
      const data = await api.getModels();
      setModels(data);
    } finally {
      setLoading(false);
    }
  };

  const filtered = models.filter((m) => {
    if (taskFilter !== 'all' && !m.taskTypes.includes(taskFilter as any)) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        m.name.toLowerCase().includes(q) ||
        m.description.toLowerCase().includes(q) ||
        m.id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleRegisterAdapter = (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName.trim() || !regId.trim()) return;

    const newAdapter: ModelAdapter = {
      id: regId.toLowerCase().replace(/\s+/g, '-'),
      name: regName,
      framework: 'scikit-learn',
      taskTypes: [regTask],
      predictProba: regTask === 'classification',
      description: regDesc || 'Custom registered scikit-learn model adapter.',
      parameters: {
        random_state: 42,
      },
    };

    setModels((prev) => [...prev, newAdapter]);
    setIsRegisterOpen(false);
    setRegName('');
    setRegId('');
    setRegDesc('');

    toast({
      type: 'success',
      title: 'Adapter Registered',
      message: `Model adapter ${newAdapter.name} is now available in Workspace.`,
    });
  };

  return (
    <AppShell showSidebar>
      <div className="max-w-6xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
          <div>
            <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white tracking-tight">
              Model Adapters
            </h1>
            <p className="text-xs sm:text-sm text-text-muted mt-1">
              Registered scikit-learn algorithmic architectures calibrated for stress testing.
            </p>
          </div>

          <Button
            variant="secondary"
            onClick={() => setIsRegisterOpen(true)}
            className="gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>Register Adapter</span>
          </Button>
        </div>

        {/* Mandated Callout */}
        <Callout type="info" title="Zero Model File Uploads">
          Model files (.pkl, .onnx, .pt) cannot be uploaded. In accordance with platform security and empirical reproducibility requirements, only verified algorithmic adapters are executed.
        </Callout>

        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between bg-surface p-3.5 rounded-xl border border-border">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 text-text-subtle absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search model adapters..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-surface-2 border border-border text-xs text-white placeholder-text-subtle focus:outline-none focus:border-white/40"
            />
          </div>

          <div className="flex items-center gap-3">
            <select
              value={taskFilter}
              onChange={(e) => setTaskFilter(e.target.value)}
              className="bg-surface-2 border border-border rounded-lg px-3 py-1.5 text-xs text-white font-cabin focus:outline-none"
            >
              <option value="all">All Tasks</option>
              <option value="classification">Classification</option>
              <option value="regression">Regression</option>
            </select>
          </div>
        </div>

        {/* Models Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="p-6 rounded-xl bg-surface border border-border space-y-4">
                <Skeleton className="h-5 w-48" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-4 w-32" />
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No model adapters found"
            description="No adapters matched your current filter criteria."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filtered.map((model) => (
              <div
                key={model.id}
                className="p-6 rounded-xl bg-surface border border-border hover:border-border-strong transition-all flex flex-col justify-between group"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-surface-2 border border-white/10 flex items-center justify-center text-white">
                        <Cpu className="w-5 h-5 text-accent" />
                      </div>
                      <div>
                        <h3 className="font-manrope font-semibold text-base text-white group-hover:text-accent transition-colors">
                          {model.name}
                        </h3>
                        <span className="font-mono text-xs text-text-subtle">{model.id}</span>
                      </div>
                    </div>

                    <Badge variant="outline" className="text-[10px] font-mono">
                      {model.framework}
                    </Badge>
                  </div>

                  <p className="text-xs text-text-muted leading-relaxed line-clamp-2">
                    {model.description}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {model.predictProba ? (
                      <span className="text-xs font-cabin text-success flex items-center gap-1.5">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        Probability Calibration
                      </span>
                    ) : (
                      <span className="text-xs font-cabin text-warning flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5" />
                        Decision Function
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Link href={`/models/${model.id}`}>
                      <Button variant="secondary" size="sm" className="gap-1.5 text-xs">
                        <span>Details</span>
                        <ArrowRight className="w-3 h-3" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Register Adapter Dialog */}
        <Dialog
          open={isRegisterOpen}
          onClose={() => setIsRegisterOpen(false)}
          title="Register New Model Adapter"
          description="Define a new scikit-learn algorithmic interface to execute stress experiments."
        >
          <form onSubmit={handleRegisterAdapter} className="space-y-4 pt-2">
            <div>
              <label className="block text-xs font-cabin uppercase text-text-subtle mb-1">
                Adapter Name
              </label>
              <input
                type="text"
                placeholder="e.g. Extra Trees Classifier"
                value={regName}
                onChange={(e) => setRegName(e.target.value)}
                required
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-white/40"
              />
            </div>

            <div>
              <label className="block text-xs font-cabin uppercase text-text-subtle mb-1">
                Adapter ID (slug)
              </label>
              <input
                type="text"
                placeholder="e.g. extra-trees-classifier"
                value={regId}
                onChange={(e) => setRegId(e.target.value)}
                required
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-white/40"
              />
            </div>

            <div>
              <label className="block text-xs font-cabin uppercase text-text-subtle mb-1">
                Task Type
              </label>
              <select
                value={regTask}
                onChange={(e) => setRegTask(e.target.value as any)}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
              >
                <option value="classification">Classification</option>
                <option value="regression">Regression</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-cabin uppercase text-text-subtle mb-1">
                Description
              </label>
              <textarea
                placeholder="One-line summary of algorithmic architecture..."
                value={regDesc}
                onChange={(e) => setRegDesc(e.target.value)}
                rows={2}
                className="w-full bg-surface-2 border border-border rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-white/5">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setIsRegisterOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm">
                Register Adapter
              </Button>
            </div>
          </form>
        </Dialog>
      </div>
    </AppShell>
  );
}
