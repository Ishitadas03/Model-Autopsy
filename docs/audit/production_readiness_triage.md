# Model Autopsy — Production Readiness Triage (code inspection)

**Inspected ref:** `main` at `20563da8696c85967a5cb1a7407df7e9c4ef69cb` (2026-11-16 inspection).  
**Remediation branch:** `fix/production-data-integrity-guardrails`.  
**Scope:** Selected high-risk code paths inspected via GitHub connector; this is **not** a complete repository audit, and no end-to-end/local or deployment tests were executed in this session.  
**Verdict:** **NOT PRODUCTION READY** until the blocking items below are repaired and demonstrated in staging.

## Confirmed, source-level defects

| Priority | File | Evidence / impact | Status |
|---|---|---|---|
| P0 | `backend/app/services/ml_engine_bridge.py` | `_parse_results` used baseline F1=0.958, synthetic curve points, Iris-only feature vulnerability and fabricated failed samples regardless of requested dataset. Scientific results were not trustworthy. | Guardrail fix proposed in this PR |
| P0 | `backend/app/services/baseline_service.py` | Missing uploaded dataset silently fell back to Iris; missing target silently fell back to last column. | Guardrail fix proposed |
| P0 | `backend/app/api/v1/endpoints/experiments.py` | `_build_results` substituted hardcoded baseline/worst scores and failure threshold for null database measurements. | Guardrail fix proposed |
| P0 | `backend/app/api/v1/endpoints/experiments.py`, `datasets.py` | No visible authentication/ownership dependencies in list/detail/create/download endpoints. Records and CSV downloads may be accessible across users unless an uninspected upstream gate prevents it. Verify deployment and implement enforceable identity/ownership checks before allowing private uploads. | Unresolved |
| P1 | `backend/app/services/experiment_service.py` | `asyncio.create_task` and class-level in-memory registry for long-running jobs; jobs are not durable across worker restart or multiple instances. | Unresolved |
| P1 | `backend/app/services/experiment_service.py` | Hardcoded severity levels, generic defaults to RF/classification, missing propagation of selected model parameters, target column, and split parameters to ML bridge. | Unresolved |
| P1 | `backend/app/services/baseline_service.py`, `scripts/experiments/run_generic.py` | Numeric and categorical imputers/encoders fit to the *full dataset before train/test split*, leaking holdout distribution into training; regression missing targets converted to zero. | Unresolved |
| P1 | `scripts/experiments/run_generic.py` | Failed sample `confidence=0.85` is hardcoded; uses classification metric field names to store regression R²/MAE. | Unresolved |
| P1 | `backend/app/services/experiment_service.py` | R2 artifact upload exception is logged and suppressed; experiment can still become completed despite incomplete durable artifact storage. | Unresolved |
| P1 | `backend/app/services/experiment_service.py` | Artifact R2 object key uses only `art['file_name']`, risking collisions across per-seed subdirectories. | Unresolved |
| P1 | `frontend/lib/api.ts` | Dataset/model API failures silently return mock catalogs, and create/cancel calls did not check HTTP errors. | Guardrail fix proposed |
| P1 | `frontend/app/workspace/page.tsx`, `frontend/components/workspace/Step5Review.tsx` | Placeholder dataset/model defaults persist in workspace; review action falls back to demo IDs, allowing inaccurate manifest contents. | Unresolved |
| P2 | `.github/workflows` | No CI workflow found (only `.gitkeep`). | Unresolved |
| P2 | `backend/app/core/config.py` | Default CORS origin regex allows any `*.vercel.app`, inconsistent with production least-privilege CORS when credentials are enabled. | Unresolved |

## Important implementation/verification observations

- `backend/app/services/ml_engine_bridge.py` runs an external subprocess from the API instance, with stdout and stderr pipes. This design needs bounded resource usage, timeouts, stderr draining, failure recovery, and durable scheduling before concurrent production workloads.
- `backend/app/services/experiment_service.py` stores some subprocess results in Supabase and uploads files to R2, but object-reference integrity under failure is not demonstrated.
- `frontend/lib/api.ts` enables explicit mocks when `NEXT_PUBLIC_USE_MOCKS=true`; deployment must prove mocks are disabled for production. Some hardcoded demo handling is present outside that condition.
- `backend/app/main.py` makes a `/health` endpoint return healthy without checking database/storage readiness.
- Existing GitHub history and audit documents contain claims of passing tests; those claims were **not independently rerun** here.

## Proposed order of remaining work

1. **P0: privacy and truthfulness.** Enforce authentication/ownership; remove all fabricated measurements; validate missing datasets and target columns; remove silent demo fallbacks.
2. **P1: scientific correctness.** Move imputation and encoding into a train-only `ColumnTransformer`/`Pipeline` shared by baseline and generic runner; validate targets; unify classification/regression metric schemas; remove fabricated sample confidence.
3. **P1: end-to-end contract.** Preserve dataset ID, target, task, selected model/hyperparameters, split, seeds, features, protocol, and severity through UI → request → database manifest → runner → results.
4. **P1: durable jobs.** Migrate execution from API-process `asyncio.create_task` to a PostgreSQL-backed leased job worker (or a justified external queue). Ensure idempotency, cancellation, heartbeat, crash recovery, per-user quotas, resource limits, timeout and retry policy.
5. **P1: storage integrity.** Make R2 artifact upload mandatory for completion in cloud mode; preserve unique per-seed object paths; verify checksum; reconcile partial writes.
6. **P2: CI and security regression suite.** Add lint, TypeScript typecheck, frontend build, backend/ML pytest, contract/security and dataset tests; gate merges on CI.
7. **Staging acceptance.** Upload binary, multiclass, and regression CSVs; execute all compatible protocols; simulate restart and storage outages; verify Supabase/R2 persistence, access isolation and browser behavior.
8. **Measured scalability.** Run permissioned staging load tests and report throughput, latency, CPU/memory peak, queue wait, job success rate and safe concurrency. No unsupported scalability claims.

## Acceptance decision

**NOT PRODUCTION READY.** This is a targeted source-based finding, not an assertion that every deployment route has been tested. The remediation branch only addresses a subset of data-integrity defects. Review and test before merge. Do not promote to production on this report alone.
