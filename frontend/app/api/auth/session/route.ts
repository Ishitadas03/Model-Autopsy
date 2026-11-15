import { NextRequest, NextResponse } from 'next/server';
import { ACCESS_COOKIE, clearSessionCookies, refreshSession, setSessionCookies } from '@/lib/server-auth';

export async function GET(request: NextRequest) {
  let access = request.cookies.get(ACCESS_COOKIE)?.value;
  let updated = null;
  if (!access) {
    updated = await refreshSession(request);
    access = updated?.access_token;
  }
  if (!access) return NextResponse.json({ authenticated: false }, { headers: { 'Cache-Control': 'no-store' } });

  const base = process.env.SUPABASE_URL?.replace(/\/$/, '');
  const anon = process.env.SUPABASE_ANON_KEY;
  if (!base || !anon) return NextResponse.json({ error: 'Auth not configured' }, { status: 503 });
  try {
    let user = await fetch(base + '/auth/v1/user', {
      headers: { apikey: anon, Authorization: 'Bearer ' + access },
      cache: 'no-store',
    });
    if (user.status === 401 && !updated) {
      updated = await refreshSession(request);
      if (updated) user = await fetch(base + '/auth/v1/user', {
        headers: { apikey: anon, Authorization: 'Bearer ' + updated.access_token }, cache: 'no-store',
      });
    }
    if (!user.ok) {
      const response = NextResponse.json({ authenticated: false }, { headers: { 'Cache-Control': 'no-store' } });
      clearSessionCookies(response);
      return response;
    }
    const data = await user.json();
    const response = NextResponse.json({ authenticated: true, id: data.id, email: data.email }, {
      headers: { 'Cache-Control': 'private, no-store' },
    });
    if (updated) setSessionCookies(response, updated);
    return response;
  } catch { return NextResponse.json({ error: 'Session temporarily unavailable' }, { status: 503 }); }
}