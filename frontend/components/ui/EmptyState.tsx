import React from 'react';
import { LucideIcon, Inbox } from 'lucide-react';
import { Button } from './Button';

export interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  actionLabel,
  onAction,
  className = '',
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center text-center p-8 border border-dashed border-white/10 rounded-card bg-surface/50 ${className}`}
    >
      <div className="p-3 rounded-full bg-white/5 text-text-subtle mb-3">
        <Icon className="w-6 h-6" aria-hidden="true" />
      </div>
      <h3 className="font-manrope font-semibold text-base text-white mb-1">
        {title}
      </h3>
      <p className="text-xs text-text-subtle max-w-sm mb-4">{description}</p>
      {actionLabel && onAction && (
        <Button variant="secondary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
