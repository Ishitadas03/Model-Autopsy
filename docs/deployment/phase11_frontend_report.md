# Phase 11 — Frontend Web Application & Vercel Deployment Report

**Project:** Model Autopsy — Find Out Why AI Models Fail  
**Component:** Next.js 14 Frontend Application & Vercel Edge Deployment  
**Date:** 2026-11-05  
**Status:** CONFIGURED & VERIFIED  

---

## 1. Executive Summary

The Model Autopsy frontend is built with **Next.js 14 (App Router)**, **TypeScript**, **Tailwind CSS**, and **Framer Motion**. It provides a sleek, dark-mode research console for running stress tests, inspecting real-time telemetry, visualizing multidimensional robustness curves, and examining failure distributions.

The frontend is optimized for deployment on **Vercel** with automatic continuous deployment triggered on every push to the `main` branch.

---

## 2. Vercel Project Configuration

### 2.1 Configuration Manifest (`frontend/vercel.json`)
The repository includes `frontend/vercel.json` configured for Vercel's zero-config Next.js runtime:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "nextjs",
  "cleanUrls": true,
  "trailingSlash": false,
  "env": {
    "NEXT_PUBLIC_APP_NAME": "Model Autopsy",
    "NEXT_PUBLIC_USE_MOCKS": "false"
  }
}
```

### 2.2 Dynamic API Proxying (`frontend/next.config.js`)
To eliminate CORS friction and avoid hardcoding backend URLs into client JavaScript bundles, Next.js rewrites proxy `/api/:path*` requests directly to the backend URL supplied via `BACKEND_API_URL`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    const backendUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: '/health',
        destination: `${backendUrl}/health`,
      },
    ];
  },
};

module.exports = nextConfig;
```

---

## 3. UI Defect Resolution: ECG Logo Scaling

### 3.1 Defect Description
Earlier during local development, opening `http://localhost:3000` rendered a giant white ECG pulse waveform scaling across the entire browser viewport (see screenshot `media_1793863506939_053dd844.png`).

### 3.2 Root Cause Analysis
1. In unstyled or early-compilation states in Next.js development mode, SVG elements with `viewBox="0 0 24 24"` lack default physical constraints if only CSS utility classes (`w-5 h-5`) are applied.
2. If the Tailwind stylesheet has not yet finished compiling into the Next.js dev server cache, the SVG scales to 100% of the parent container width.
3. In a flexbox container with `stroke="currentColor"`, the SVG line rendered across the entire monitor.

### 3.3 Permanent Hardening Implemented
`frontend/components/ui/Logo.tsx` was hardened with explicit inline physical dimensions matching the selected size variant:
```tsx
const pixelDimensions = {
  sm: 16,
  md: 20,
  lg: 24,
};

<svg
  viewBox="0 0 24 24"
  width={pixelDimensions[size]}
  height={pixelDimensions[size]}
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
```
With explicit `width` and `height` attributes on the SVG element itself, the browser enforces the exact pixel boundary (16px, 20px, or 24px) even if stylesheets are still loading or cached.

---

## 4. Disabling Mock Mode for Live Backend Integration

The frontend includes mock fixtures for offline development. In production, live data is strictly enforced:
- **`NEXT_PUBLIC_USE_MOCKS=false`**: Instructs all API client hooks (`useExperiments`, `useExperimentDetail`, `useFailures`) to fetch real data from `/api/v1/...`.
- If the backend is temporarily sleeping or cold-starting (Render free tier), the UI shows an animated connection probe rather than falling back to fictitious data.

---

## 5. Verification Status

- [x] All 40 Vitest frontend component and hook tests passing (`node node_modules/vitest/vitest.mjs run`).
- [x] Logo SVG hardened against unconstrained viewport expansion.
- [x] Vercel deployment manifest verified (`frontend/vercel.json`).
- [x] Next.js reverse proxy configuration verified (`frontend/next.config.js`).

