# Supabase migration preflight — Model Autopsy (2026-11-16)

**Scope:** existing Supabase project `zrdkttqstkjpviyplpdd`. This is an evidence-based inspection, **not an executed database migration**. Do not use a newly created paid database or paid branching without authorization.

## Confirmed live facts (read-only Supabase SQL and advisors)

- Project was inactive, restored on 2026-11-16, and reached `ACTIVE_HEALTHY`.
- Current Alembic revision is **`001_initial_tables`** (one revision row).
- Existing records **must be retained**: datasets **2**, model adapters **4**, experiments **10**, experiment runs **50**, experiment results **8**, failed samples **120**, artifact manifests **269**, artifact references **0**.
- `auth.users` currently contains **0** users. This means two-account *live* ownership checks cannot yet be performed.
- Core 8 application tables have RLS enabled but **no explicit policies**. `public.alembic_version` also has RLS enabled without a policy; that migration history table should not have a browser-visible SELECT policy.
- The SECURITY DEFINER function `public.rls_auto_enable()` was executable by anonymous and authenticated roles. The staged migration **004** revokes public/direct execution after creating tenant policies; this has **not** been applied.
- Database schema has no `datasets.owner_id` / `experiments.owner_id` columns yet.

## Data safety gate — REQUIRED BEFORE APPLYING MIGRATIONS

1. Securely create a **full logical backup** using `pg_dump` from a trusted Windows machine. Script: `scripts/backup_supabase_before_migration.ps1`. Confirm backup SHA-256, secure storage and a **successful restore into an independent scratch PostgreSQL 17 database**. Do not commit or upload the dump.
2. Keep a separate backup of the current R2 dataset/object bucket and preserve object hashes/manifests; the database alone does not contain the uploaded CSVs or all reports.
3. Reconcile live data counts, FK constraints and table/index naming against revision `001`. Verify there are no added custom schemas or policies that would make the migration drift.
4. Test `002_tenant_security`, `003_durable_jobs` and `004_tenant_rls` in order on the restored database. Ensure old custom data stays **owner_id=NULL** and inaccessible to new accounts. Do **not** assign old records to the first person who signs in.
5. Inspect the migration output, count all rows again and run PostgreSQL policy tests under different authenticated subjects. Verify direct PostgREST clients cannot perform writes and can read only their own user-owned rows/public benchmarks.
6. Only then take the migration into production. The FastAPI API deliberately fails readiness if the revision is not `004_tenant_rls`.
7. Validate real login/signup on Vercel against the same Supabase project, JWT signing with **RS256/ES256** (the backend intentionally does not accept legacy HS256), R2 persistence and Render Free embedded job recovery.

## Read-only verification SQL (safe to run from Supabase SQL Editor)

```sql
SELECT version_num FROM public.alembic_version;
SELECT (SELECT count(*) FROM public.datasets) datasets,
       (SELECT count(*) FROM public.experiments) experiments,
       (SELECT count(*) FROM public.experiment_runs) experiment_runs,
       (SELECT count(*) FROM public.experiment_results) experiment_results,
       (SELECT count(*) FROM public.failed_samples) failed_samples,
       (SELECT count(*) FROM public.artifact_manifests) artifact_manifests;
SELECT tablename, policyname, cmd, roles
FROM pg_catalog.pg_policies
WHERE schemaname = 'public'
  AND tablename IN (
    'datasets','model_adapters','experiments','experiment_runs',
    'experiment_results','failed_samples','artifact_manifests','artifact_references'
  )
ORDER BY tablename, policyname;
```

## Release hold

**Do not merge PR #7 while these gates remain unverified.** Render currently deploys from `main`, so a merge would publish code expecting `004` and user sessions; without the schema and credentials, the new application would fail. This release must stay staged until the verified backup and production migration are complete.
