import { NextRequest, NextResponse } from 'next/server';
import { setSessionCookies, supabaseRequest, validSameOrigin } from '@/lib/server-auth';

export async function POST(request: NextRequest) {
  if (!validSameOrigin(request)) return NextResponse.json({ error: 'Forbidden origin' }, { status: 403 });
  let body: Record<string, unknown>;
  try { body = await request.json(); } catch { return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 }); }
  if (typeof body?.email !== 'string' || typeof body?.password !== 'string' ||
      !body.email.includes('@') || body.email.length > 254 || body.password.length < 8 || body.password.length > 1024)
    return NextResponse.json({ error: 'Valid email and password (8+ characters) required' }, { status: 400 });
  try {
    const auth = await supabaseRequest('signup', { email: body.email, password: body.password });
    const result = await auth.json().catch(() => ({}));
    if (!auth.ok) return NextResponse.json({ error: 'Unable to sign up. Check email/password or try again later.' }, { status: 400 });
    const response = NextResponse.json({
      confirmationRequired: !result.access_token,
      authenticated: Boolean(result.access_token),
    }, { status: result.access_token ? 201 : 202, headers: { 'Cache-Control': 'no-store' } });
    if (result.access_token && result.refresh_token) setSessionCookies(response, result);
    return response;
  } catch { return NextResponse.json({ error: 'Authentication service unavailable' }, { status: 503 }); }
}