import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'accent' | 'success' | 'warning' | 'info';
  size?: 'sm' | 'md';
}

export function Badge({
  children,
  className = '',
  variant = 'default',
  size = 'md',
  ...props
}: BadgeProps) {
  const base =
    'inline-flex items-center font-cabin font-medium tracking-wide uppercase transition-colors';

  const sizes = {
    sm: 'text-[10px] px-2 py-0.5 rounded-full',
    md: 'text-xs px-2.5 py-1 rounded-full',
  };

  const variants = {
    default: 'bg-surface-2 text-text border border-white/10',
    outline: 'bg-transparent text-text-muted border border-white/20',
    accent: 'bg-accent/10 text-accent border border-accent/30',
    success: 'bg-success/10 text-success border border-success/30',
    warning: 'bg-warning/10 text-warning border border-warning/30',
    info: 'bg-info/10 text-info border border-info/30',
  };

  return (
    <span className={`${base} ${sizes[size]} ${variants[variant]} ${className}`} {...props}>
      {children}
    </span>
  );
}
