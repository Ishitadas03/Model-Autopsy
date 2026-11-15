'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');

  useEffect(() => {
    let active = true;
    if (process.env.NEXT_PUBLIC_USE_MOCKS === 'true') {
      setState('ready');
      return;
    }
    fetch('/api/auth/session', { cache: 'no-store', credentials: 'same-origin' })
      .then(async response => {
        if (!active) return;
        if (response.status === 503) {
          setState('error');
          return;
        }
        const body = await response.json();
        if (body.authenticated) setState('ready');
        else router.replace('/login');
      })
      .catch(() => { if (active) setState('error'); });
    return () => { active = false; };
  }, [router]);

  if (state === 'loading') return (
    <div role="status" className="min-h-screen flex items-center justify-center text-text-muted">
      Checking your session…
    </div>
  );
  if (state === 'error') return (
    <div role="alert" className="min-h-screen flex items-center justify-center text-red-400">
      Authentication is temporarily unavailable. Please refresh to retry.
    </div>
  );
  return <>{children}</>;
}
