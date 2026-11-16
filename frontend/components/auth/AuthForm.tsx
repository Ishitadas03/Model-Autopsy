'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export function AuthForm({ mode }: { mode: 'login' | 'signup' }) {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [working, setWorking] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (working) return;
    setWorking(true);
    setError('');
    setInfo('');
    try {
      const response = await fetch('/api/auth/' + mode, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
        credentials: 'same-origin',
      });
      const result = await response.json();
      if (!response.ok) {
        setError(result.error || 'Authentication failed. Please try again.');
      } else if (result.confirmationRequired) {
        setInfo('Check your email for the confirmation link. After verifying, sign in.');
      } else {
        router.replace('/experiments');
        router.refresh();
      }
    } catch {
      setError('Cannot reach the authentication service. Try again later.');
    } finally {
      setWorking(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-5 py-16">
      <div className="w-full max-w-md rounded-2xl border border-border bg-surface p-8 shadow-2xl">
        <Link href="/" className="font-manrope text-xl font-bold text-white">
          Model <span className="text-accent">Autopsy</span>
        </Link>
        <h1 className="mt-8 text-2xl font-semibold text-white">
          {mode === 'login' ? 'Sign in to your workspace' : 'Create your account'}
        </h1>
        <p className="mt-2 text-sm text-text-muted">
          Your datasets, experiments and reports belong to your account.
        </p>
        <form onSubmit={submit} className="mt-7 space-y-4">
          <label className="block text-sm text-white" htmlFor="auth-email">
            Email address
            <input id="auth-email" type="email" name="email" autoComplete="email" required
              maxLength={254} value={email} onChange={e => setEmail(e.target.value)}
              className="mt-2 w-full rounded-lg border border-border bg-surface-2 px-4 py-3 text-white outline-none focus:border-accent"
              placeholder="you@example.com" />
          </label>
          <label className="block text-sm text-white" htmlFor="auth-password">
            Password
            <input id="auth-password" type="password" name="password"
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required minLength={mode === 'signup' ? 8 : undefined} maxLength={1024}
              value={password} onChange={e => setPassword(e.target.value)}
              className="mt-2 w-full rounded-lg border border-border bg-surface-2 px-4 py-3 text-white outline-none focus:border-accent" />
          </label>
          {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
          {info && <p role="status" className="text-sm text-green-400">{info}</p>}
          <button type="submit" disabled={working}
            className="w-full rounded-lg bg-accent px-4 py-3 font-semibold text-white transition hover:opacity-90 disabled:opacity-50">
            {working ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>
        <p className="mt-6 text-sm text-text-muted">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <Link href={mode === 'login' ? '/signup' : '/login'} className="text-white underline underline-offset-4">
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </Link>
        </p>
      </div>
    </main>
  );
}
