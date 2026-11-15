# Model Autopsy — Production rollout v2 (NOT yet approved for deployment)

This document corresponds to draft PR #7. **Do not merge or deploy** until the gates below are satisfied. The new web app deliberately rejects requests if required auth, database migration or durable R2 storage is absent. The worker is a **separate always-on service**, not a task created by the web request.

## Architecture and required accounts

- Frontend: Next.js 14 on Vercel, with server-side auth/session routes and an authenticated same-origin API proxy.
- API: FastAPI on Render. It validates Supabase Auth asymmetric JWT signatures against the project's JWKS.
- Database: existing Supabase PostgreSQL. Alembic versions 001 -> 002 -> 003.
- Object store: Cloudflare R2, required for production CSVs and experiment artifacts.
- ML execution: separate Render background worker running `PYTHONPATH=backend python -m app.workers.experiment_worker`, with database row locks, leases, cancellation polling, crash detection and timeout protection.
- Existing users: legacy custom dataset/experiment records have **NULL owner_id** and remain quarantined; do not assign random owners. Only explicitly identified public benchmark datasets are shared.

## Critical authorization prerequisite

Confirm that the Supabase project uses **asymmetric JWT signing keys** supported by the backend JWKS verifier (RS256 / ES256); a project still using an HS256 legacy JWT secret is not supported by this release. Configure verified email signup and provider URL settings. Never move a signing secret or service-role key into browser environment variables.

## Environment configuration

**Vercel frontend (server-side, not NEXT_PUBLIC):**
- `SUPABASE_URL` — official Supabase project URL
- `SUPABASE_ANON_KEY` — publishable/anon key (used only server-side in this implementation)
- `BACKEND_API_URL` — production Render HTTPS origin
- `NEXT_PUBLIC_USE_MOCKS=false`

**Render API:**
- `APP_ENV=production`
- `AUTH_REQUIRED=true`
- `SUPABASE_URL=<project-url>`
- `JOB_EXECUTION_MODE=worker`
- `STORAGE_PROVIDER=r2`
- `DATABASE_URL=<existing Supabase asyncpg DSN with TLS>`
- `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` and if needed `R2_ENDPOINT_URL`
- `CORS_ORIGINS=https://model-autopsy-ai.vercel.app` (plus intentional localhost origins for development only)
- `CORS_ORIGIN_REGEX` empty/unset.

**Render worker:**
Use same database/R2/ML configuration as API, with `JOB_EXECUTION_MODE=worker`, `MAX_CONCURRENT_EXPERIMENTS=1` and bounded `EXPERIMENT_TIMEOUT_SECONDS`. Start one worker instance first; increase worker count only after measuring resource usage. **Render background worker service may incur recurring charges; obtain the account owner's confirmation before creating it.**

## Non-destructive database migration

1. Create and validate a database backup/snapshot. Note the current `alembic_version` and number of rows in datasets/experiments/artifact tables.
2. Rehearse migration in a staging database populated from a sanitized snapshot. Verify that only named benchmark datasets become public and that legacy custom rows stay unowned.
3. Run `cd backend && alembic upgrade head` from a trusted environment using a secure DB connection. Verify revision `003_durable_jobs`; do **not** run `Base.metadata.create_all()` in production.
4. Inspect and tighten existing Supabase **direct API RLS policies** before releasing authenticated browser clients. Application-level ownership checks do not prove that PostgREST policies are safe. Disable direct browser table access or explicitly define and test tenant policies for every table.
5. Deploy backend with `/api/ready` as its health gate; the route must report all checks true. Start the durable worker only after API and storage are verified.
6. Deploy frontend with secure server-only auth variables, then test fresh signup, confirmation, login, refresh, logout, CSV upload, experiments and downloads.

## Staging acceptance matrix

- Two distinct accounts: user A cannot list, download, inspect, cancel or read user B's experiments, failure samples, reports or datasets. Check requests by both numeric/UUID and human-readable IDs.
- Upload separate numeric/categorical CSVs for binary, multiclass and regression tasks; verify registration, exact target selection, SHA-256 and R2 persistent retrieval after restart.
- Verify Gaussian and MCAR experiments actually use selected model params, split, seeds and target columns. Unsupported stress modes must be explicitly blocked, not silently replaced.
- Verify regression results contain real `r2`, `mae`, `rmse`; no regression scores under F1/accuracy, no invented confidence/sample failures.
- Submit two experiments simultaneously, force cancel one, restart worker mid-run, verify DB lease expiry becomes FAILED (not stuck RUNNING), and confirm no double results.
- During R2 outage or partial artifact upload, do not mark jobs completed; check error/rollback/reconciliation and read-back checksums.
- Run permissioned load tests with CPU, memory, queue delay, concurrency, failure rate, DB pool and p95/p99 latency; record real capacity boundaries.
- Confirm frontend Next.js production build and deployed SHA, backend deployed SHA, /api/ready, worker logs and error monitoring.

## Known limitations / holdbacks

- CI tests validate code paths but do not prove live Supabase, Render, R2 or Vercel deployment correctness.
- Feature corruption, E004 cross-run sample persistence, E005 causal claims, structured stress mode and distribution shift remain unsupported by the generic experiment runner. The UI must not claim they work until implemented/validated.
- The worker does not automatically replay a possibly side-effecting failed job; it marks lease-expired jobs FAILED and requires verified manual retry. Blind automatic retries risk duplicate artifacts.
- Global worker concurrency, billing, dataset size ceilings, tenancy RLS and dependency vulnerability audit need staging validation.
- Next.js 14.2.15 is old and requires a dedicated tested dependency upgrade with a regenerated lockfile.

## Rollback plan

Stop accepting new experiment submissions; stop worker gracefully; keep encrypted snapshot and exported run/artifact manifest. Redeploy prior Vercel/Render SHAs if needed. **Do not automatically reverse database migrations** while data created under the new schema exists. Reconcile ownership and artifacts before considering rollback migrations.

## Verdict

Code changes are staged in draft PR #7. **NOT PRODUCTION READY** until migration rehearsal, security isolation, worker deployment, credential configuration, CI, and live staged E2E checks are all successful.
