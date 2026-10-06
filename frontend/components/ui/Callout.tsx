import React from 'react';
import { Info, AlertTriangle, ShieldAlert, Sparkles } from 'lucide-react';

export interface CalloutProps {
  type?: 'info' | 'warning' | 'caveat' | 'honesty';
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Callout({
  type = 'info',
  title,
  children,
  className = '',
}: CalloutProps) {
  const configs = {
    info: {
      icon: <Info className="w-4 h-4 text-info flex-shrink-0 mt-0.5" aria-hidden="true" />,
      border: 'border-info/30',
      bg: 'bg-info/5',
      titleColor: 'text-info',
    },
    warning: {
      icon: <AlertTriangle className="w-4 h-4 text-warning flex-shrink-0 mt-0.5" aria-hidden="true" />,
      border: 'border-warning/30',
      bg: 'bg-warning/5',
      titleColor: 'text-warning',
    },
    caveat: {
      icon: <ShieldAlert className="w-4 h-4 text-accent flex-shrink-0 mt-0.5" aria-hidden="true" />,
      border: 'border-accent/30',
      bg: 'bg-accent/5',
      titleColor: 'text-accent',
    },
    honesty: {
      icon: <Sparkles className="w-4 h-4 text-white/80 flex-shrink-0 mt-0.5" aria-hidden="true" />,
      border: 'border-white/20',
      bg: 'bg-white/5',
      titleColor: 'text-white',
    },
  };

  const current = configs[type];

  return (
    <div
      className={`flex items-start gap-3 p-3.5 rounded-card border ${current.border} ${current.bg} text-xs text-text-muted ${className}`}
    >
      {current.icon}
      <div className="flex-1">
        {title && (
          <p className={`font-semibold ${current.titleColor} mb-0.5`}>{title}</p>
        )}
        <div className="leading-relaxed">{children}</div>
      </div>
    </div>
  );
}
