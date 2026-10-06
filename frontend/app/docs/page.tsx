'use client';

import React from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ArrowLeft, BookOpen, ShieldCheck, Terminal, Cpu } from 'lucide-react';

export default function DocsPage() {
  return (
    <AppShell>
      <div className="max-w-4xl mx-auto space-y-8 py-6">
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="sm" className="gap-1.5 text-xs">
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Home</span>
            </Button>
          </Link>
          <Badge variant="outline">Documentation</Badge>
        </div>

        <div>
          <h1 className="font-manrope font-bold text-3xl md:text-4xl text-white">
            Model Autopsy Architecture & Specifications
          </h1>
          <p className="text-sm text-text-muted mt-2">
            A comprehensive reference for reproducible model stress-testing, robustness metrics, and boundary detection.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card className="p-6 space-y-3">
            <div className="p-2.5 rounded-lg bg-surface-2 border border-white/10 w-fit text-accent">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h2 className="font-manrope font-semibold text-base text-white">
              Controlled Perturbation Design
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              Stress tests are applied strictly to the evaluation split. The training set and preprocessing pipelines are never touched by perturbations, ensuring zero data leakage and authentic empirical degradation measurement.
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="p-2.5 rounded-lg bg-surface-2 border border-white/10 w-fit text-info">
              <Terminal className="w-5 h-5" />
            </div>
            <h2 className="font-manrope font-semibold text-base text-white">
              Observed Failure Boundaries
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              The platform calculates the exact severity threshold where model performance breaches pre-configured limits. Labeled with exact rigor: &ldquo;Observed failure boundary under the specified experimental configuration.&rdquo;
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="p-2.5 rounded-lg bg-surface-2 border border-white/10 w-fit text-warning">
              <Cpu className="w-5 h-5" />
            </div>
            <h2 className="font-manrope font-semibold text-base text-white">
              Adapter-Based Model Sandboxing
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              To eliminate malicious bytecode and remote execution vulnerabilities, Model Autopsy does not accept arbitrary serialized model files. Only native scikit-learn verified adapters are instantiated.
            </p>
          </Card>

          <Card className="p-6 space-y-3">
            <div className="p-2.5 rounded-lg bg-surface-2 border border-white/10 w-fit text-success">
              <BookOpen className="w-5 h-5" />
            </div>
            <h2 className="font-manrope font-semibold text-base text-white">
              Direction-Aware Degradation
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              Bounded classification metrics (F1, Accuracy) distinguish percentage points (pp) from relative decay (%). Regression metrics (MAE, RMSE) explicitly model lower-is-better failure vectors.
            </p>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
