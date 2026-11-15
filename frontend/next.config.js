/** @type {import('next').NextConfig} */
const backendApiUrl =
  process.env.BACKEND_API_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  (process.env.NODE_ENV === 'production'
    ? 'https://model-autopsy-backend.onrender.com'
    : 'http://127.0.0.1:8000');

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['three'],
  // API traffic is authenticated and proxied by app/api/[...path]/route.ts.
  // A Next.js rewrite could forward requests without server-side session checks.

};

module.exports = nextConfig;
