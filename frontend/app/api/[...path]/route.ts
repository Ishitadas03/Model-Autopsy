import { NextRequest, NextResponse } from 'next/server';
import { ACCESS_COOKIE, clearSessionCookies, refreshSession, setSessionCookies, validSameOrigin } from '@/lib/server-auth';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const WRITE_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

async function proxy(request: NextRequest, context: { params: { path: string[] } }) {
  const method = request.method;
  if (WRITE_METHODS.has(method) && !validSameOrigin(request)) {
    return NextResponse.json({ error: 'Forbidden origin' }, { status: 403 });
  }
  const parts = context.params.path;
  if (!Array.isArray(parts) || !parts.length || parts.some((part) => !/^[a-zA-Z0-9_.-]{1,160}$/.test(part) || part === '..')) {
    return NextResponse.json({ error: 'Invalid API path' }, { status: 400 });
  }
  const backend = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL ||
      'https://model-autopsy-backend.onrender.com';
  if (!backend.startsWith('https://') && process.env.NODE_ENV === 'production') {
    return NextResponse.json({ error: 'Invalid backend configuration' }, { status: 503 });
  }
  const publicRead = method === 'GET' && (parts[0] === 'health' || parts[0] === 'models');
  let token = request.cookies.get(ACCESS_COOKIE)?.value;
  let refreshed = null;
  if (!token && !publicRead) {
    refreshed = await refreshSession(request);
    token = refreshed?.access_token;
  }
  if (!token && !publicRead) return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
  const path = parts.map(encodeURIComponent).join('/');
  const target = backend.replace(/\/$/, '') + '/api/v1/' + path + request.nextUrl.search;
  const headers = new Headers({ Accept: request.headers.get('accept') || 'application/json' });
  if (token) headers.set('Authorization', 'Bearer ' + token);
  const contentType = request.headers.get('content-type');
  if (contentType) headers.set('Content-Type', contentType);
  let body: ArrayBuffer | undefined;
  if (WRITE_METHODS.has(method)) {
    const raw = await request.arrayBuffer();
    if (raw.byteLength > 21 * 1024 * 1024) return NextResponse.json({ error: 'Payload too large' }, { status: 413 });
    body = raw;
  }
  const execute = (access?: string) => {
    if (access) headers.set('Authorization', 'Bearer ' + access);
    return fetch(target, { method, headers, body, cache: 'no-store', signal: AbortSignal.timeout(180000) });
  };
  try {
    let upstream = await execute(token);
    if (upstream.status === 401 && !publicRead && !refreshed) {
      refreshed = await refreshSession(request);
      if (refreshed) upstream = await execute(refreshed.access_token);
    }
    const response = new NextResponse(upstream.body, {
      status: upstream.status,
      headers: {
        'Content-Type': upstream.headers.get('content-type') || 'application/octet-stream',
        'Cache-Control': 'private, no-store',
        ...(upstream.headers.get('content-disposition') ? { 'Content-Disposition': upstream.headers.get('content-disposition')! } : {}),
        ...(upstream.headers.get('x-sha256') ? { 'X-SHA256': upstream.headers.get('x-sha256')! } : {}),
      },
    });
    if (refreshed) setSessionCookies(response, refreshed);
    if (upstream.status === 401 && !refreshed) clearSessionCookies(response);
    return response;
  } catch {
    return NextResponse.json({ error: 'Backend temporarily unavailable' }, { status: 502 });
  }
}
export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
