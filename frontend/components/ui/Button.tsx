import React from 'react';
import { ArrowRight, Loader2 } from 'lucide-react';

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'destructive' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  withArrow?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className = '',
      variant = 'primary',
      size = 'md',
      loading = false,
      withArrow = false,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-cabin font-medium transition-all duration-200 select-none disabled:opacity-50 disabled:pointer-events-none group';

    const variants = {
      primary:
        'bg-white text-[#0a0a0a] hover:bg-[#e8e8e8] active:scale-[0.98] shadow-sm',
      secondary:
        'bg-transparent text-white border border-white/20 hover:border-white/50 hover:bg-white/5 active:scale-[0.98]',
      destructive:
        'bg-transparent text-accent border border-accent/40 hover:bg-accent/10 hover:border-accent active:scale-[0.98]',
      ghost:
        'bg-transparent text-text-muted hover:text-white hover:bg-white/5 active:scale-[0.98]',
    };

    const sizes = {
      sm: 'h-8 px-3 text-xs rounded-[8px] gap-1.5',
      md: 'h-10 px-4 text-sm rounded-[10px] gap-2',
      lg: 'h-12 px-6 text-base rounded-[10px] gap-2.5',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
        {...props}
      >
        {loading && (
          <Loader2 className="w-4 h-4 animate-spin text-current" aria-hidden="true" />
        )}
        <span>{children}</span>
        {withArrow && !loading && (
          <ArrowRight
            className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1"
            aria-hidden="true"
          />
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
