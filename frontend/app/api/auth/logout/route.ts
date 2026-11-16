import { NextRequest, NextResponse } from 'next/server';
import { ACCESS_COOKIE, clearSessionCookies, supabaseRequest, validSameOrigin } from '@/lib/server-auth';

export async function POST(request: NextRequest) {
  if (!validSameOrigin(request)) return NextResponse.json({ error: 'Forbidden origin' }, { status: 403 });
  const access = request.cookies.get(ACCESS_COOKIE)?.value;
  if (access) {
    try { await supabaseRequest('logout', {}, access); } catch { /* Clear cookies even during provider outage */ }
  }
  const result = NextResponse.json({ authenticated: false }, { headers: { 'Cache-Control': 'no-store' } });
  clearSessionCookies(result);
  return result;
}