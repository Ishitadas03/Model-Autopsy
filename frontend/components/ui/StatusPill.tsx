import React from 'react';
import {
  Clock,
  Loader2,
  CheckCircle2,
  AlertCircle,
  XCircle,
  FileEdit,
} from 'lucide-react';
import { RunStatus } from '@/lib/schemas';

interface StatusPillProps {
  status: RunStatus;
  className?: string;
}

export function StatusPill({ status, className = '' }: StatusPillProps) {
  const configs: Record<
    RunStatus,
    { label: string; icon: React.ReactNode; bg: string; text: string; border: string }
  > = {
    draft: {
      label: 'Draft',
      icon: <FileEdit className="w-3.5 h-3.5" aria-hidden="true" />,
      bg: 'bg-white/5',
      text: 'text-text-muted',
      border: 'border-white/10',
    },
    queued: {
      label: 'Queued',
      icon: <Clock className="w-3.5 h-3.5" aria-hidden="true" />,
      bg: 'bg-info/10',
      text: 'text-info',
      border: 'border-info/30',
    },
    running: {
      label: 'Running',
      icon: <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" />,
      bg: 'bg-warning/10',
      text: 'text-warning',
      border: 'border-warning/30',
    },
    completed: {
      label: 'Completed',
      icon: <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />,
      bg: 'bg-success/10',
      text: 'text-success',
      border: 'border-success/30',
    },
    failed: {
      label: 'Failed',
      icon: <AlertCircle className="w-3.5 h-3.5" aria-hidden="true" />,
      bg: 'bg-accent/10',
      text: 'text-accent',
      border: 'border-accent/40',
    },
    cancelled: {
      label: 'Cancelled',
      icon: <XCircle className="w-3.5 h-3.5" aria-hidden="true" />,
      bg: 'bg-white/5',
      text: 'text-text-subtle',
      border: 'border-white/10',
    },
  };

  const current = configs[status] || configs.draft;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-cabin font-medium border ${current.bg} ${current.text} ${current.border} ${className}`}
      role="status"
      aria-label={`Status: ${current.label}`}
    >
      {current.icon}
      <span>{current.label}</span>
    </span>
  );
}
