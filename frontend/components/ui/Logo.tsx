import React from 'react';
import Link from 'next/link';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function Logo({ className = '', size = 'md' }: LogoProps) {
  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <Link
      href="/"
      className={`inline-flex items-center gap-2.5 group select-none ${className}`}
      aria-label="Model Autopsy Home"
    >
      <div className="relative flex items-center justify-center p-1.5 rounded-md bg-surface-2 border border-white/10 group-hover:border-accent/40 transition-colors">
        {/* ECG pulse line mark */}
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`${iconSizes[size]} text-accent transition-transform duration-300 group-hover:scale-105`}
          aria-hidden="true"
        >
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      </div>

      <span
        className={`font-manrope font-bold uppercase tracking-[0.18em] text-white ${textSizes[size]}`}
      >
        Model Autopsy
      </span>
    </Link>
  );
}
