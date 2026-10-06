'use client';

import React, { useState } from 'react';
import { AppShell } from '@/components/layout/AppShell';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { StatusPill } from '@/components/ui/StatusPill';
import { Card } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { Tabs } from '@/components/ui/Tabs';
import { Input, SearchInput } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Switch } from '@/components/ui/Switch';
import { Slider } from '@/components/ui/Slider';
import { Dialog } from '@/components/ui/Dialog';
import { Drawer } from '@/components/ui/Drawer';
import { Tooltip } from '@/components/ui/Tooltip';
import { Callout } from '@/components/ui/Callout';
import { Table, TableHeader, TableHead, TableBody, TableRow, TableCell } from '@/components/ui/Table';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Skeleton } from '@/components/ui/Skeleton';
import { useToast } from '@/components/ui/Toast';
import { HERO_EXPERIMENT } from '@/lib/mocks/experiments';
import {
  MANDATED_BOUNDARY_CAPTION,
  FEATURE_VULNERABILITY_CAVEAT,
  calculateDegradation,
} from '@/lib/metrics';

export default function KitchenSinkPage() {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('components');
  const [searchValue, setSearchValue] = useState('');
  const [switchState, setSwitchState] = useState(true);
  const [sliderVal, setSliderVal] = useState(23.1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [sidebarToggle, setSidebarToggle] = useState(true);

  // Demonstrate direction-aware metric calculation
  const f1Degradation = calculateDegradation('f1', 0.958, 0.712);
  const maeDegradation = calculateDegradation('mae', 12.4, 21.8);

  const tabs = [
    { id: 'components', label: 'Components' },
    { id: 'metrics', label: 'Metrics & Honesty' },
    { id: 'tokens', label: 'Tokens & Typography' },
  ];

  return (
    <AppShell showSidebar={sidebarToggle} experimentId="EXP-0241">
      <div className="space-y-8 max-w-5xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="accent">Dev Lab</Badge>
              <span className="text-xs text-text-subtle font-mono">/dev/ui</span>
            </div>
            <h1 className="font-manrope font-bold text-3xl text-white">
              UI System Kitchen Sink
            </h1>
            <p className="text-sm text-text-muted mt-1">
              Design tokens, motion primitives, shared UI components, and honesty checks.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Switch
              checked={sidebarToggle}
              onChange={setSidebarToggle}
              label="Toggle Sidebar"
            />
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                toast({
                  type: 'info',
                  title: 'Notification Triggered',
                  message: 'Design system toast working smoothly.',
                });
              }}
            >
              Test Toast
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <Tabs tabs={tabs} activeId={activeTab} onChange={setActiveTab} />

        {/* Tab 1: Components */}
        {activeTab === 'components' && (
          <div className="space-y-8">
            {/* Buttons Section */}
            <Card className="p-6 space-y-4">
              <h2 className="font-manrope font-semibold text-lg text-white">
                Buttons & States
              </h2>
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="primary">Primary Action</Button>
                <Button variant="primary" withArrow>
                  With Arrow
                </Button>
                <Button variant="secondary">Secondary Action</Button>
                <Button variant="destructive">Destructive / Cancel</Button>
                <Button variant="ghost">Ghost Button</Button>
                <Button variant="primary" loading>
                  Loading
                </Button>
                <Button variant="primary" disabled>
                  Disabled
                </Button>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <Button size="sm">Small (sm)</Button>
                <Button size="md">Medium (md)</Button>
                <Button size="lg">Large (lg)</Button>
              </div>
            </Card>

            {/* Status Pills Section */}
            <Card className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-manrope font-semibold text-lg text-white">
                  Status Pills (Icon + Text Mandatory)
                </h2>
                <span className="text-xs text-text-subtle">WCAG AA Compliant</span>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <StatusPill status="draft" />
                <StatusPill status="queued" />
                <StatusPill status="running" />
                <StatusPill status="completed" />
                <StatusPill status="failed" />
                <StatusPill status="cancelled" />
              </div>
            </Card>

            {/* Form Controls Section */}
            <Card className="p-6 space-y-6">
              <h2 className="font-manrope font-semibold text-lg text-white">
                Form Controls
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Dataset Title"
                  placeholder="e.g. Credit Risk Benchmark"
                  id="demo-input"
                />
                <SearchInput
                  value={searchValue}
                  onChange={(e) => setSearchValue(e.target.value)}
                  onClear={() => setSearchValue('')}
                  placeholder="Search experiments..."
                />
                <Select
                  label="Stress Family"
                  id="demo-select"
                  options={[
                    { value: 'gaussian', label: 'Gaussian Noise' },
                    { value: 'missingness', label: 'Missingness' },
                    { value: 'outliers', label: 'Outliers (Coming Soon)' },
                  ]}
                />
                <div className="space-y-4">
                  <Slider
                    label="Noise Severity Threshold"
                    value={sliderVal}
                    onChange={setSliderVal}
                    min={0}
                    max={100}
                    step={0.1}
                    unit="%"
                  />
                  <div className="flex items-center gap-6">
                    <Switch
                      checked={switchState}
                      onChange={setSwitchState}
                      label="Apply evaluation stress only"
                    />
                    <Tooltip content="Tooltip showing accessible contextual documentation">
                      <span className="text-xs text-text-subtle underline cursor-help">
                        Hover for Tooltip
                      </span>
                    </Tooltip>
                  </div>
                </div>
              </div>
            </Card>

            {/* Modals & Drawers */}
            <Card className="p-6 space-y-4">
              <h2 className="font-manrope font-semibold text-lg text-white">
                Dialog & Drawer Modals
              </h2>
              <div className="flex items-center gap-4">
                <Button variant="secondary" onClick={() => setDialogOpen(true)}>
                  Open Dialog Modal
                </Button>
                <Button variant="secondary" onClick={() => setDrawerOpen(true)}>
                  Open Side Drawer
                </Button>
              </div>

              <Dialog
                open={dialogOpen}
                onClose={() => setDialogOpen(false)}
                title="Cancel Experiment EXP-0241?"
                description="This will immediately halt all running stress evaluations."
              >
                <p className="text-sm text-text-muted mb-6">
                  Are you sure you want to cancel? Progress recorded up to the current severity level will be preserved as a partial run.
                </p>
                <div className="flex justify-end gap-3">
                  <Button variant="ghost" onClick={() => setDialogOpen(false)}>
                    Dismiss
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => {
                      setDialogOpen(false);
                      toast({
                        type: 'error',
                        title: 'Cancelled',
                        message: 'Experiment EXP-0241 has been cancelled.',
                      });
                    }}
                  >
                    Confirm Cancellation
                  </Button>
                </div>
              </Dialog>

              <Drawer
                open={drawerOpen}
                onClose={() => setDrawerOpen(false)}
                title="Sample Analysis Drawer"
              >
                <div className="space-y-4 text-sm text-text-muted">
                  <p>
                    Inspect misclassified sample features, model confidence scores, and perturbation deltas.
                  </p>
                  <Callout type="info">
                    Only sample identifiers and selected features are displayed. Raw records are protected.
                  </Callout>
                  <div className="space-y-2 pt-4">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-3/4" />
                    <Skeleton className="h-8 w-1/2" />
                  </div>
                </div>
              </Drawer>
            </Card>

            {/* Table & Empty/Error States */}
            <div className="space-y-4">
              <h2 className="font-manrope font-semibold text-lg text-white">
                Tabular Display & Fallbacks
              </h2>
              <Table>
                <TableHeader>
                  <tr>
                    <TableHead>Experiment ID</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Dataset</TableHead>
                    <TableHead>Baseline</TableHead>
                    <TableHead>Degradation</TableHead>
                    <TableHead>Status</TableHead>
                  </tr>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-mono text-white">EXP-0241</TableCell>
                    <TableCell>Random Forest</TableCell>
                    <TableCell>Credit Risk Demo</TableCell>
                    <TableCell className="font-semibold text-white">95.8%</TableCell>
                    <TableCell className="text-accent font-medium">−24.6 pp</TableCell>
                    <TableCell>
                      <StatusPill status="completed" />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-mono text-white">EXP-0102</TableCell>
                    <TableCell>Logistic Regression</TableCell>
                    <TableCell>Iris</TableCell>
                    <TableCell className="font-semibold text-white">96.7%</TableCell>
                    <TableCell className="text-accent font-medium">−13.4 pp</TableCell>
                    <TableCell>
                      <StatusPill status="completed" />
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                <EmptyState
                  title="No experiments found"
                  description="Try adjusting your filters or create a new model autopsy."
                  actionLabel="Create Autopsy"
                  onAction={() => {}}
                />
                <ErrorState
                  title="Evaluation failed"
                  message="Loss diverged to NaN during stress evaluation at 10% outlier severity."
                  onRetry={() => {}}
                />
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Metrics & Honesty */}
        {activeTab === 'metrics' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                label="Baseline F1"
                value={95.8}
                suffix="%"
                decimals={1}
              />
              <StatCard
                label="Worst Case F1"
                value={71.2}
                suffix="%"
                decimals={1}
              />
              <StatCard
                label="Degradation"
                value={24.6}
                prefix="−"
                suffix=" pp"
                decimals={1}
                secondaryText="−25.7% rel"
                isDegraded={true}
              />
              <StatCard
                label="Failure Boundary"
                value={23.1}
                prefix="≈ "
                suffix="%"
                decimals={1}
                caption={MANDATED_BOUNDARY_CAPTION}
              />
            </div>

            {/* Regression Lower-Is-Better Check */}
            <Card className="p-6 space-y-4">
              <h2 className="font-manrope font-semibold text-lg text-white">
                Direction-Aware Metric Testing
              </h2>
              <p className="text-xs text-text-muted">
                Ensures MAE/RMSE (lower is better) correctly registers increases as degradation, while F1/Accuracy (higher is better) registers decreases as degradation.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-surface-2 rounded-[8px] space-y-2 border border-white/5">
                  <p className="text-xs font-semibold text-white">
                    Classification F1 (0.958 → 0.712)
                  </p>
                  <p className="text-xs font-mono text-text-muted">
                    Display: <span className="text-accent">{f1Degradation.displayText}</span>
                  </p>
                  <p className="text-xs text-text-subtle">
                    Degraded: {f1Degradation.isDegraded ? 'YES (Correct)' : 'NO'}
                  </p>
                </div>

                <div className="p-4 bg-surface-2 rounded-[8px] space-y-2 border border-white/5">
                  <p className="text-xs font-semibold text-white">
                    Regression MAE (12.4 → 21.8)
                  </p>
                  <p className="text-xs font-mono text-text-muted">
                    Display: <span className="text-accent">{maeDegradation.displayText}</span>
                  </p>
                  <p className="text-xs text-text-subtle">
                    Degraded: {maeDegradation.isDegraded ? 'YES (Correct)' : 'NO'}
                  </p>
                </div>
              </div>
            </Card>

            {/* Mandated Honesty Callouts */}
            <div className="space-y-3">
              <h2 className="font-manrope font-semibold text-lg text-white">
                Mandated Honesty Statements
              </h2>
              <Callout type="honesty" title="Exact Failure Boundary Caption">
                {MANDATED_BOUNDARY_CAPTION}
              </Callout>
              <Callout type="caveat" title="Empirical Sensitivity Caveat">
                {FEATURE_VULNERABILITY_CAVEAT}
              </Callout>
              <Callout type="warning" title="Model Upload Restriction">
                Model files cannot be uploaded. Only supported adapters are available.
              </Callout>
              <Callout type="info" title="Statistical Validation Constraint">
                Single seed — no uncertainty estimate (shown when n_seeds = 1).
              </Callout>
            </div>
          </div>
        )}

        {/* Tab 3: Tokens & Typography */}
        {activeTab === 'tokens' && (
          <div className="space-y-6">
            <Card className="p-6 space-y-4">
              <h2 className="font-manrope font-semibold text-lg text-white">
                Typography Roles
              </h2>
              <div className="space-y-4">
                <div>
                  <span className="text-[10px] font-mono text-text-subtle uppercase">
                    Instrument Serif (Landing Hero Headline & Report Cover)
                  </span>
                  <p className="font-serif text-4xl text-white italic">
                    Find out why AI Models <span className="text-accent">Fail.</span>
                  </p>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-text-subtle uppercase">
                    Manrope 700 / 600 (UI Titles, Navigation, Stat Numbers)
                  </span>
                  <p className="font-manrope font-bold text-2xl text-white">
                    Autopsy Workspace & Robustness Dashboard
                  </p>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-text-subtle uppercase">
                    Cabin 600 (Buttons, Tags, Eyebrow Labels)
                  </span>
                  <p className="font-cabin font-semibold text-sm uppercase tracking-wider text-text-muted">
                    AI MODEL RELIABILITY LAB • RESEARCH PHASE
                  </p>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-text-subtle uppercase">
                    Inter 400 (Body, Descriptions, Tables)
                  </span>
                  <p className="font-inter text-sm text-text-muted">
                    Systematically stress-test machine learning models, measure their robustness, and discover the conditions where their performance breaks down.
                  </p>
                </div>
              </div>
            </Card>

            <Card className="p-6 space-y-4">
              <h2 className="font-manrope font-semibold text-lg text-white">
                Theme Color Palette Tokens
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-bg border border-border">
                  <span className="text-text-subtle">--bg</span>
                  <p className="font-mono text-white mt-1">#050506</p>
                </div>
                <div className="p-3 rounded-lg bg-surface border border-border">
                  <span className="text-text-subtle">--surface</span>
                  <p className="font-mono text-white mt-1">#0c0c0f</p>
                </div>
                <div className="p-3 rounded-lg bg-surface-2 border border-border">
                  <span className="text-text-subtle">--surface-2</span>
                  <p className="font-mono text-white mt-1">#131318</p>
                </div>
                <div className="p-3 rounded-lg bg-accent/20 border border-accent/40 text-accent">
                  <span>--accent</span>
                  <p className="font-mono text-white mt-1">#ef4444</p>
                </div>
                <div className="p-3 rounded-lg bg-success/20 border border-success/40 text-success">
                  <span>--success</span>
                  <p className="font-mono text-white mt-1">#22c55e</p>
                </div>
                <div className="p-3 rounded-lg bg-warning/20 border border-warning/40 text-warning">
                  <span>--warning</span>
                  <p className="font-mono text-white mt-1">#f59e0b</p>
                </div>
                <div className="p-3 rounded-lg bg-info/20 border border-info/40 text-info">
                  <span>--info</span>
                  <p className="font-mono text-white mt-1">#60a5fa</p>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </AppShell>
  );
}
