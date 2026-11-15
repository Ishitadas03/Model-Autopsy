import { NextRequest, NextResponse } from 'next/server';

export const ACCESS_COOKIE = 'ma_access';
export const REFRESH_COOKIE = 'ma_refresh';

type SessionTokens = { access_token: string; refresh_token: string; expires_in: number; token_type?: string };

function supabaseConfig() {
  const url = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const anonKey = process.env.SUPABASE_ANON_KEY;
  if (!url || !anonKey) throw new Error('Authentication provider is not configured');
  return { url, anonKey };
}

export function validSameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get('origin');
  if (!origin) return false;
  try { return new URL(origin).origin === request.nextUrl.origin; }
  catch { return false; }
}

export async function supabaseRequest(path: string, payload: unknown, accessToken?: string): Promise<Response> {
  const { url, anonKey } = supabaseConfig();
  return fetch(url + '/auth/v1/' + path, {
    method: 'POST',
    headers: {
      'apikey': anonKey,
      'Content-Type': 'application/json',
      ...(accessToken ? { Authorization: 'Bearer ' + accessToken } : {}),
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
    signal: AbortSignal.timeout(10000),
  });
}

export function setSessionCookies(response: NextResponse, tokens: SessionTokens) {
  const secure = process.env.NODE_ENV === 'production';
  response.cookies.set(ACCESS_COOKIE, tokens.access_token, {
    httpOnly: true, secure, sameSite: 'lax', path: '/', maxAge: Math.max(30, tokens.expires_in - 60),
  });
  response.cookies.set(REFRESH_COOKIE, tokens.refresh_token, {
    httpOnly: true, secure, sameSite: 'lax', path: '/', maxAge: 7 * 24 * 60 * 60,
  });
}

export function clearSessionCookies(response: NextResponse) {
  for (const cookie of [ACCESS_COOKIE, REFRESH_COOKIE]) {
    response.cookies.set(cookie, '', { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax', path: '/', maxAge: 0 });
  }
}

export async function refreshSession(request: NextRequest): Promise<SessionTokens | null> {
  const token = request.cookies.get(REFRESH_COOKIE)?.value;
  if (!token) return null;
  try {
    const result = await supabaseRequest('token?grant_type=refresh_token', { refresh_token: token });
    if (!result.ok) return null;
    const json = await result.json();
    if (typeof json.access_token !== 'string' || typeof json.refresh_token !== 'string') return null;
    return json as SessionTokens;
  } catch { return null; }
}
