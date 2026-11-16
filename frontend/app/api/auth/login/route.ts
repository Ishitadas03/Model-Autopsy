import { NextRequest, NextResponse } from 'next/server';
import { setSessionCookies, supabaseRequest, validSameOrigin } from '@/lib/server-auth';

export async function POST(request: NextRequest) {
  if (!validSameOrigin(request)) return NextResponse.json({ error: 'Forbidden origin' }, { status: 403 });
  let payload: unknown;
  try { payload = await request.json(); } catch { return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 }); }
  const body = payload as Record<string, unknown>;
  if (typeof body?.email !== 'string' || typeof body?.password !== 'string' ||
      body.email.length > 254 || body.password.length > 1024) {
    return NextResponse.json({ error: 'Valid email and password are required' }, { status: 400 });
  }
  try {
    const auth = await supabaseRequest('token?grant_type=password', { email: body.email, password: body.password });
    if (!auth.ok) return NextResponse.json({ error: 'Invalid email or password' }, { status: 401 });
    const tokens = await auth.json();
    if (!tokens.access_token || !tokens.refresh_token)
      return NextResponse.json({ error: 'Authentication session unavailable' }, { status: 503 });
    const response = NextResponse.json({ authenticated: true }, { headers: { 'Cache-Control': 'no-store' } });
    setSessionCookies(response, tokens);
    return response;
  } catch { return NextResponse.json({ error: 'Authentication service unavailable' }, { status: 503 }); }
}