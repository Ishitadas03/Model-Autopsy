# Model Autopsy — ₹0 deployment path

**Status:** staged in draft PR #7. No paid service has been created or enabled.
This is a **limited demonstration deployment**, not a guarantee of 24/7 background processing.

## Architecture

- **Vercel Free:** Next.js frontend; server-side login/signup and HttpOnly session cookies.
- **Render Free web service:** FastAPI **plus embedded PostgreSQL-backed queue poller** in the same web instance (`JOB_EXECUTION_MODE=embedded`). This avoids a separate paid background worker.
- **Supabase Free:** existing PostgreSQL metadata, job status, tenant ownership and Supabase Auth (subject to free-tier quotas).
- **Cloudflare R2 free allowance:** encrypted object bucket for uploaded datasets, report outputs and artifacts (usage must stay within the provider's current free allowance).

No Kubernetes, paid Redis, Render Starter, always-on worker, external cron, or third-party uptime pinger is required or recommended.

## Important operational limits

1. The free web instance may sleep when idle, be restarted or have limited CPU/memory. **Queued jobs won't be processed while the instance is asleep**. Jobs in progress can be interrupted; a previous RUNNING job will be marked FAILED after its lease expires when a worker becomes active again. Manual resubmission is required.
2. The embedded loop intentionally runs **at most one experiment at a time per web process**. Keep the Render service configured for **one web process**, no `uvicorn --workers N` in the free setup.
3. Default limits: CSV file up to **3 MiB**, up to **5,000 rows**, up to **2 seeds**, up to **7 stress levels** and up to **2 active (queued+running) experiments per user**. The API enforces them; the UI must surface errors clearly.
4. Default ML timeout is **420 seconds**. A timeout or restart does not imply a scientifically valid result.
5. Free service levels are not appropriate for long-running compute, guaranteed deadlines, high concurrency or large datasets.
6. Never create a paid Render background worker without explicit authorization.

## Existing Render service

`model-autopsy-backend` (`srv-dbm8pql9fdbs73c652u0`) currently auto-deploys `main`. **Do not merge PR #7** until the migration and environment gates below pass. The service's existing health probe `/health` only verifies process liveness; the new `/api/ready` gate checks production prerequisites.

## Render environment variables

Set on the **existing** free web service after a staging rehearsal:

```text
APP_ENV=production
AUTH_REQUIRED=true
JOB_EXECUTION_MODE=embedded
STORAGE_PROVIDER=r2
EXPERIMENT_TIMEOUT_SECONDS=420
WORKER_LEASE_SECONDS=90
WORKER_POLL_SECONDS=3
EMBEDDED_MAX_SEEDS=2
EMBEDDED_MAX_SEVERITIES=7
EMBEDDED_MAX_ACTIVE_JOBS_PER_USER=2
EMBEDDED_MAX_CSV_BYTES=3145728
EMBEDDED_MAX_CSV_ROWS=5000
```

Also preserve/review existing `DATABASE_URL`, `SUPABASE_URL` and R2 credentials. Use the **existing actual bucket name**, which may differ from the example value in `render.yaml`; never silently switch buckets. Keep secrets in Render environment variables, never Git.

Vercel server-side: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `BACKEND_API_URL`; browser setting `NEXT_PUBLIC_USE_MOCKS=false`. Confirm Supabase Auth uses compatible asymmetric JWT signing.

## Safe production rollout order

1. Verify the GitHub Actions CI on the PR's **latest commit**; frontend typecheck/build, backend/ML pytest all green.
2. Back up the existing Supabase DB; inspect the **actual** `alembic_version`, indexes, rows and RLS configuration. Check whether migration 001 matches the live schema, and do not blindly stamp/alter it.
3. Rehearse revisions `002_tenant_security` and `003_durable_jobs` in staging using a sanitized copy. Verify that legacy private uploads remain inaccessible, anonymous requests return 401 and two users cannot access each other's rows.
4. Apply reviewed migrations only after verifying a working backup and current schema compatibility.
5. Configure auth and R2 on Render and Vercel, set embedded execution on the **existing** free service, then merge/deploy only with all gates passed. Check `/api/ready`, deployed SHAs and startup logs.
6. E2E exercise the entire workflow on small classification and regression CSVs, including restart/cancellation and R2 artifact download after restart; monitor memory and CPU.
7. Check real free-tier usage, quota and timeout behavior. Revisit limits before inviting outside users.

## Verification versus claims

CI passing verifies code under test only. It does **not** prove the migration is safe on the actual Supabase database, that the real Vercel/Render configuration matches the repo, or that a sleeping free worker runs without interruption.

**Do not claim uninterrupted, truly scalable production service with this free-tier architecture.** It is best described as a publicly accessible, secure-if-verified demonstration SaaS for small workloads.
