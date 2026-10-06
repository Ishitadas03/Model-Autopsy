'use client';

import React, { useEffect, useState } from 'react';
import { api, HealthResponse } from '@/lib/api';

export function CommandStatus({ className = '' }: { className?: string }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    let mounted = true;
    api
      .getHealth()
      .then((res) => {
        if (mounted) setHealth(res);
      })
      .catch(() => {
        if (mounted)
          setHealth({ status: 'error', mode: 'mock', version: '0.1.0' });
      });
    return () => {
      mounted = false;
    };
  }, []);

  const isMock = health?.mode === 'mock';

  return (
    <div
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-2 border border-white/10 text-[11px] font-cabin tracking-wide select-none ${className}`}
      title={
        isMock
          ? 'Running on typed internal mock API (NEXT_PUBLIC_USE_MOCKS=true)'
          : 'Connected to live backend'
      }
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          health?.status === 'ok'
            ? isMock
              ? 'bg-info animate-pulse'
              : 'bg-success'
            : 'bg-accent'
        }`}
        aria-hidden="true"
      />
      <span className="text-text-subtle font-medium">API:</span>
      <span className="text-white font-semibold uppercase">
        {health?.mode || 'MOCK'}
      </span>
    </div>
  );
}
