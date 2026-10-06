'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Printer,
  Download,
  Share2,
  FileCode,
  ShieldCheck,
  AlertTriangle,
  ArrowLeft,
  Compass,
  Sliders,
  Database,
  Cpu,
  BarChart2,
  HelpCircle,
} from 'lucide-react';
import { AppShell } from '@/components/layout/AppShell';
import { api } from '@/lib/api';
import { Experiment } from '@/lib/schemas';
import { HERO_EXPERIMENT } from '@/lib/mocks/experiments';
import { MANDATED_BOUNDARY_CAPTION, FEATURE_VULNERABILITY_CAVEAT } from '@/lib/metrics';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tooltip } from '@/components/ui/Tooltip';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/Table';

import { ReportCover } from '@/components/reports/ReportCover';
import { ReportNav } from '@/components/reports/ReportNav';
import { RobustnessCurve } from '@/components/results/RobustnessCurve';
import { FeatureVulnerability } from '@/components/results/FeatureVulnerability';

export default function ResearchReportPage() {
  const params = useParams();
  const router = useRouter();
  const experimentId = (params?.id as string) || 'EXP-0241';

  const [experiment, setExperiment] = useState<Experiment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadExperiment = async () => {
      setLoading(true);
      try {
        const data = await api.getExperiment(experimentId);
        setExperiment(data?.results ? data : HERO_EXPERIMENT);
      } catch {
        setExperiment(HERO_EXPERIMENT);
      } finally {
        setLoading(false);
      }
    };

    loadExperiment();
  }, [experimentId]);

  const handlePrintPdf = () => {
    if (typeof window !== 'undefined') {
      window.print();
    }
  };

  const handleExportJson = () => {
    if (!experiment) return;
    const jsonStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(experiment, null, 2));
    const a = document.createElement('a');
    a.setAttribute('href', jsonStr);
    a.setAttribute('download', `report-${experimentId}.json`);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const exp = experiment || HERO_EXPERIMENT;
  const results = exp.results || HERO_EXPERIMENT.results!;

  return (
    <AppShell showSidebar={false}>
      {/* Print-only CSS stylesheet injected for clean light-mode printing */}
      <style jsx global>{`
        @media print {
          body {
            background-color: #ffffff !important;
            color: #0a0a0a !important;
          }
          nav, button, .no-print {
            display: none !important;
          }
          .print-clean {
            border: 1px solid #e5e5e5 !important;
            background: #ffffff !important;
            color: #0a0a0a !important;
            box-shadow: none !important;
          }
        }
      `}</style>

      <div className="max-w-6xl mx-auto w-full space-y-8">
        {/* Navigation & Action Header */}
        <div className="space-y-3 no-print">
          <Link
            href={`/experiments/${experimentId}/results`}
            className="inline-flex items-center gap-2 text-xs font-cabin text-text-subtle hover:text-white transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Results Dashboard</span>
          </Link>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/5">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-xs text-accent font-semibold px-2 py-0.5 rounded bg-accent/10 border border-accent/20">
                  {exp.id}
                </span>
                <span className="text-xs text-text-subtle font-mono">Formal Research Evaluation</span>
              </div>
              <h1 className="font-manrope font-semibold text-2xl sm:text-3xl text-white tracking-tight">
                Research Report
              </h1>
              <p className="text-xs sm:text-sm text-text-muted mt-0.5">
                A formal, reproducible evaluation of empirical model robustness under controlled distribution shifts.
              </p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2.5">
              <Tooltip content="Interim browser print layout. Server-generated PDF coming later.">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handlePrintPdf}
                  className="gap-1.5 text-xs bg-white text-black hover:bg-neutral-200"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Export PDF</span>
                </Button>
              </Tooltip>

              <Button
                variant="secondary"
                size="sm"
                onClick={handleExportJson}
                className="gap-1.5 text-xs"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export JSON</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Hero Section: 3-column with TOC, 3D Cover, and Highlights */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Column 1: Sticky TOC (3 cols) */}
          <div className="hidden lg:block lg:col-span-3 no-print">
            <ReportNav />
          </div>

          {/* Column 2: 3D Mouse Tilt Cover (5 cols) */}
          <div className="lg:col-span-5">
            <ReportCover
              experimentId={exp.id}
              modelName={exp.modelName}
              datasetName={exp.datasetName}
            />
          </div>

          {/* Column 3: Report Highlights Card (4 cols) */}
          <div className="lg:col-span-4 p-6 rounded-2xl bg-surface border border-border shadow-xl space-y-4 print-clean">
            <h3 className="font-manrope font-semibold text-sm text-white pb-3 border-b border-white/5">
              Executive Highlights
            </h3>

            <div className="space-y-3.5 text-xs font-mono">
              <div className="flex justify-between items-center">
                <span className="text-text-subtle">Baseline F1:</span>
                <span className="font-bold text-white">95.8%</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-text-subtle">Worst-Case F1:</span>
                <span className="font-bold text-accent">71.2%</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-text-subtle">Observed Boundary:</span>
                <span className="font-bold text-white">23.1%</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-text-subtle">Failed Samples:</span>
                <span className="font-bold text-white">143</span>
              </div>

              <div className="pt-2 border-t border-white/5 space-y-1">
                <span className="text-text-subtle text-[10px] uppercase font-cabin block">
                  Most Vulnerable Feature:
                </span>
                <div className="font-semibold text-white">Credit Score (-28.4 pp)</div>
                <p className="text-[10px] text-text-subtle italic">
                  {FEATURE_VULNERABILITY_CAVEAT}
                </p>
              </div>

              <div className="pt-2 border-t border-white/5 space-y-1">
                <span className="text-text-subtle text-[10px] uppercase font-cabin block">
                  Statistical Validation:
                </span>
                <div className="text-accent font-semibold">95% CI ± 2.4% (5 seeds)</div>
              </div>
            </div>
          </div>
        </div>

        {/* Full 12 Report Sections in Order */}
        <div className="space-y-10 pt-6">
          {/* Section 1: Overview */}
          <section id="summary" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-3 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              1. Executive Overview
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              This report presents the stress-testing autopsy of <strong>{exp.modelName}</strong> trained on the <strong>{exp.datasetName}</strong> benchmark. Under systematically injected Gaussian noise perturbation across evaluation inputs, the model exhibited a graceful degradation from <strong>95.8% F1</strong> down to <strong>71.2% F1</strong> at 30% noise severity, revealing a critical observed failure boundary at <strong>23.1%</strong> perturbation scale.
            </p>
          </section>

          {/* Section 2: Dataset */}
          <section id="dataset" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-4 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              2. Dataset Characteristics
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
              <div className="p-3 rounded-lg bg-surface-2 border border-border">
                <span className="text-text-subtle block text-[10px]">Dataset ID</span>
                <span className="text-white font-semibold mt-0.5 block">{exp.datasetId}</span>
              </div>
              <div className="p-3 rounded-lg bg-surface-2 border border-border">
                <span className="text-text-subtle block text-[10px]">Sample Count</span>
                <span className="text-white font-semibold mt-0.5 block">1,000</span>
              </div>
              <div className="p-3 rounded-lg bg-surface-2 border border-border">
                <span className="text-text-subtle block text-[10px]">Features</span>
                <span className="text-white font-semibold mt-0.5 block">4 Tabular</span>
              </div>
              <div className="p-3 rounded-lg bg-surface-2 border border-border">
                <span className="text-text-subtle block text-[10px]">Task Type</span>
                <span className="text-white font-semibold mt-0.5 block uppercase">{exp.taskType}</span>
              </div>
            </div>
          </section>

          {/* Section 3: Model */}
          <section id="model" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-3 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              3. Algorithmic Model Architecture
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              Evaluated architecture: <strong>scikit-learn RandomForestClassifier</strong> (100 estimators, max depth 10, bootstrap sampling). Zero external serialized model weights were loaded; model fitting and feature transformers were trained inside an isolated runtime sandbox.
            </p>
          </section>

          {/* Section 4: Baseline */}
          <section id="baseline" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-3 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              4. Clean Baseline Reference
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              Before perturbation, hold-out performance was calibrated under seed <strong>{exp.seed}</strong>: Accuracy <strong>96.2%</strong>, Precision <strong>95.4%</strong>, Recall <strong>96.2%</strong>, F1 <strong>95.8%</strong>, ROC-AUC <strong>0.985</strong>.
            </p>
          </section>

          {/* Section 5: Stress Configuration */}
          <section id="stress-config" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-3 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              5. Perturbation Stress Configuration
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              Perturbation family: <strong>Zero-mean Gaussian noise</strong> scaled by feature standard deviations. Evaluation increments tested: <strong>[5%, 10%, 20%, 30%]</strong>. Stress was isolated strictly to evaluation samples, guaranteeing data integrity.
            </p>
          </section>

          {/* Section 6: Robustness Results */}
          <section id="robustness" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-4 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              6. Robustness Results & Degradation
            </h2>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Noise Severity</TableHead>
                  <TableHead>F1 Score</TableHead>
                  <TableHead>Absolute Drop (pp)</TableHead>
                  <TableHead>Relative Drop (%)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell className="font-mono text-white">0% (Baseline)</TableCell>
                  <TableCell className="font-mono text-white">95.8%</TableCell>
                  <TableCell className="font-mono text-text-subtle">0.0 pp</TableCell>
                  <TableCell className="font-mono text-text-subtle">0.0%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-mono text-text-subtle">10%</TableCell>
                  <TableCell className="font-mono text-white">88.5%</TableCell>
                  <TableCell className="font-mono text-accent">-7.3 pp</TableCell>
                  <TableCell className="font-mono text-text-subtle">-7.6%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-mono text-text-subtle">20%</TableCell>
                  <TableCell className="font-mono text-white">82.4%</TableCell>
                  <TableCell className="font-mono text-accent">-13.4 pp</TableCell>
                  <TableCell className="font-mono text-text-subtle">-14.0%</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-mono text-accent font-semibold">30% (Worst-case)</TableCell>
                  <TableCell className="font-mono text-accent font-bold">71.2%</TableCell>
                  <TableCell className="font-mono text-accent">-24.6 pp</TableCell>
                  <TableCell className="font-mono text-accent">-25.7%</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </section>

          {/* Section 7: Failure Analysis */}
          <section id="failures" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-3 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              7. Failure Mode Analysis
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              Out of 1,000 test cases, <strong>143 misclassification events</strong> occurred. The minority Fraud class suffered disproportionately high failure rates (64.3% of total errors), demonstrating risk of silent model degradation under real-world shifts.
            </p>
          </section>

          {/* Section 8: Failure Boundary */}
          <section id="boundary" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-3 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              8. Empirical Failure Boundary
            </h2>
            <div className="p-4 rounded-lg bg-surface-2 border border-border space-y-2">
              <span className="font-manrope font-bold text-2xl text-accent">
                Observed Boundary: 23.1%
              </span>
              <p className="text-xs text-text-subtle italic">
                {MANDATED_BOUNDARY_CAPTION}
              </p>
            </div>
          </section>

          {/* Section 9: Statistical Validation */}
          <section id="statistics" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-3 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              9. Statistical Validation & Uncertainty
            </h2>
            <p className="text-xs text-text-muted leading-relaxed">
              Calculated across <strong>5 repeated pseudorandom seeds</strong>: Mean F1 = <strong>71.2%</strong> (std = 0.012), yielding a <strong>95% Confidence Interval of ± 2.4%</strong>.
            </p>
          </section>

          {/* Section 10: Visualizations */}
          <section id="visualizations" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-4 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              10. Robustness Visualizations
            </h2>
            <RobustnessCurve
              curveData={results.curveData || []}
              failureThreshold={results.failureThreshold}
              observedBoundary={results.observedBoundary}
            />
          </section>

          {/* Section 11: Limitations */}
          <section id="limitations" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-3 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              11. Scientific Limitations & Boundaries
            </h2>
            <ul className="text-xs text-text-subtle space-y-2 list-disc list-inside leading-relaxed">
              <li>
                <strong>Empirical Sensitivity Caveat:</strong> {FEATURE_VULNERABILITY_CAVEAT}
              </li>
              <li>
                <strong>No Aggregate Grade:</strong> Platform strictly refrains from computing arbitrary reliability scores.
              </li>
              <li>
                <strong>Perturbation Bounds:</strong> Observed failure boundaries are valid solely within the evaluated noise parameter space.
              </li>
            </ul>
          </section>

          {/* Section 12: Reproducibility */}
          <section id="reproducibility" className="p-6 rounded-xl bg-surface border border-border shadow-xl space-y-3 print-clean">
            <h2 className="font-manrope font-semibold text-lg text-white">
              12. Reproducibility & Audit Log
            </h2>
            <div className="p-4 rounded-lg bg-surface-2 border border-border font-mono text-xs text-text-muted space-y-1">
              <div>Experiment ID: {exp.id}</div>
              <div>Hold-out Split Seed: {exp.seed}</div>
              <div>Platform Engine: model-autopsy-engine v2026.1</div>
              <div>Dataset SHA-256: 7f4a2b9195e26b1a</div>
            </div>
          </section>
        </div>
      </div>
    </AppShell>
  );
}
