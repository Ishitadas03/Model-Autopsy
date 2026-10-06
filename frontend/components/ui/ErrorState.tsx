import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  className = '',
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={`flex flex-col items-center justify-center text-center p-8 border border-accent/20 rounded-card bg-accent/5 ${className}`}
    >
      <div className="p-3 rounded-full bg-accent/10 text-accent mb-3">
        <AlertCircle className="w-6 h-6" aria-hidden="true" />
      </div>
      <h3 className="font-manrope font-semibold text-base text-white mb-1">
        {title}
      </h3>
      <p className="text-xs text-text-muted max-w-sm mb-4">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} className="gap-2">
          <RotateCcw className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Try Again</span>
        </Button>
      )}
    </div>
  );
}
