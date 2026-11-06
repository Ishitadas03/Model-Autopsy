# Full System Integration & End-to-End Architectural Audit

**Date:** November 6, 2026  
**Auditor:** Model Autopsy Senior Architecture & Engineering Team  
**Scope:** Complete End-to-End System (`frontend/`, `backend/`, `ml_engine/`, Supabase PostgreSQL, Cloudflare R2, Vercel, Render)  
**Target Services:**
- **Frontend:** `https://model-autopsy-ai.vercel.app` (Vercel)
- **Backend API & ML Runtime:** `https://model-autopsy-backend.onrender.com` (Render)
- **Database:** Supabase PostgreSQL (`aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres`)
- **Object Storage:** Cloudflare R2 bucket `project9` (Account `916b7f70128acc095b09c70a1c1d6318`)
- **Git HEAD Commit:** `03a1793`

---

## 1. Service Dependency & Communication Map

```mermaid
flowchart TD
    subgraph ClientBrowser [Client Web Browser]
        UI[Next.js 14 React UI]
        State[Zustand & React State]
    end

    subgraph VercelEdge [Vercel Edge Platform]
        EdgeRewrites["next.config.js /api/:path* rewrites"]
        ServerlessE003["app/api/experiments/e003/route.ts"]
    end

    subgraph RenderContainer [Render Linux Container]
        FastAPI["FastAPI Backend (Uvicorn)"]
        MLBridge["ml_engine_bridge.py Subprocess Runner"]
        MLEngine["Python ML Engine (/ml_engine)"]
        StorageAdapter["storage_service.py (boto3)"]
    end

    subgraph CloudflareCloud [Cloudflare Object Storage]
        R2Bucket["Cloudflare R2 Bucket (project9)"]
    end

    subgraph SupabaseCloud [Supabase Cloud Managed Services]
        PostgresDB[(Supabase PostgreSQL 15)]
    end

    UI -->|Browser Fetch /api/...| EdgeRewrites
    EdgeRewrites -->|Reverse Proxy HTTP/HTTPS| FastAPI
    UI -.->|Direct Route Hijack| ServerlessE003

    FastAPI -->|Async SQLAlchemy / asyncpg + SSL| PostgresDB
    FastAPI -->|Async Subprocess Exec| MLBridge
    MLBridge -->|In-Process Execution| MLEngine

    FastAPI -->|S3 API (boto3) / HTTPS| R2Bucket
    MLEngine -->|Generates Local Artifacts| FastAPI
    FastAPI -->|Uploads results.json, curves.csv, report.md| R2Bucket
    FastAPI -->|Persists Artifact References & Hashes| PostgresDB

    UI -->|Downloads Presigned URL / 307 Redirect| R2Bucket
```

---

## 2. Comprehensive Subsystem Audit Findings

### 2.1 Frontend Subsystem (`frontend/`)

1. **Mock Mode Defaulting & Bypass of Live Backend:**
   - **File:** `frontend/lib/api.ts` (lines 7–10)
   - **Root Cause:**
     ```typescript
     const USE_MOCKS =
       typeof window !== 'undefined'
         ? process.env.NEXT_PUBLIC_USE_MOCKS !== 'false'
         : true;
     ```
     Because `NEXT_PUBLIC_USE_MOCKS` is `undefined` by default in Vercel production unless explicitly added, `USE_MOCKS` evaluates to `true` on the client side.
   - **Impact:** Live users interact with static mock arrays (`MOCK_EXPERIMENTS`, `MOCK_DATASETS`, `MOCK_MODELS`, `MOCK_FAILED_SAMPLES`) in browser memory. Live backend experiments and datasets are never queried or displayed.
   - **Remediation:** Invert default: mock mode must only be active if `process.env.NEXT_PUBLIC_USE_MOCKS === 'true'`. In production, default must be live API communication.

2. **Next.js Rewrite Fallback to `127.0.0.1:8000`:**
   - **File:** `frontend/next.config.js` (lines 2–5)
   - **Root Cause:**
     ```javascript
     const backendApiUrl =
       process.env.BACKEND_API_URL ||
       process.env.NEXT_PUBLIC_BACKEND_URL ||
       'http://127.0.0.1:8000';
     ```
     If `BACKEND_API_URL` or `NEXT_PUBLIC_BACKEND_URL` is omitted in Vercel environment variables, Next.js serverless proxy rewrites forward to localhost (`127.0.0.1:8000`), which fails with connection refused on Vercel.
   - **Remediation:** Provide production fallback default: `https://model-autopsy-backend.onrender.com`.

3. **Local Route Shadowing Real Backend Artifacts:**
   - **File:** `frontend/app/api/experiments/e003/route.ts`
   - **Root Cause:** Next.js matches local filesystem routes before applying `rewrites()` in `next.config.js`. This route attempts to read `artifacts/experiments/E003/` from the Vercel serverless container disk via `fs.existsSync(artifactPath)`, returning 404 when the local file is not bundled with the serverless function.
   - **Remediation:** Remove local shadow route or update it to proxy directly to `${backendApiUrl}/api/v1/experiments/e003`.

4. **Simulated Dataset Upload in Workspace UI:**
   - **File:** `frontend/components/workspace/Step1Dataset.tsx` (lines 88–121)
   - **Root Cause:** When a user uploads a CSV, `handleFileUpload` sets a fake timer (`setTimeout`), fabricates a fake schema (`840 samples, 6 features`), and assigns a fake ID (`custom-${Date.now()}`). The CSV bytes are never uploaded to `POST /api/v1/datasets/upload`.
   - **Impact:** The dataset is never persisted to Cloudflare R2 or Supabase. Any experiment referencing this custom dataset fails upon execution.
   - **Remediation:** Connect `Step1Dataset.tsx` to `POST /api/v1/datasets/upload` using `FormData` and populate real inferred features from the backend response.

5. **Client-Side Progress Simulation & One-Shot Polling:**
   - **File:** `frontend/hooks/useRunStatus.ts` (lines 73–91)
   - **Root Cause:** `fetchStatus()` was called once on mount. Progress percent was incremented by an interval timer adding pseudo-random numbers (`prev + Math.floor(Math.random() * 5) + 3`) until reaching 100%, regardless of whether the backend experiment was still queued, running, or failed.
   - **Remediation:** Implement real polling interval (`setInterval(fetchStatus, 2500)`) syncing `progressPercent`, `status`, and `error` directly with the backend.

6. **Silent Fallback to `HERO_EXPERIMENT` on Real Experiment Views:**
   - **Files:** `frontend/app/experiments/[id]/results/page.tsx` & `report/page.tsx`
   - **Root Cause:** `setExperiment(data?.results ? data : HERO_EXPERIMENT)` silently suppressed real empty/error states and displayed pre-canned benchmark data.
   - **Remediation:** Display real experiment state; render explicit loading or failed state if the run was unsuccessful.

7. **Reports Directory Hardcoded to Mocks:**
   - **File:** `frontend/app/reports/page.tsx` (line 12)
   - **Root Cause:** `const completedExperiments = MOCK_EXPERIMENTS.filter((e) => e.status === 'completed');` bypassed the backend API completely.
   - **Remediation:** Fetch real completed experiments from `api.getExperiments()`.

---

### 2.2 Backend Subsystem (`backend/`)

1. **CORS Explicit Origin Matching:**
   - **File:** `backend/app/core/config.py`
   - **Finding:** `CORS_ORIGIN_REGEX` permitted `^https://.*\.vercel\.app$`, but `CORS_ORIGINS` only listed `http://localhost:3000`.
   - **Remediation:** Explicitly include `https://model-autopsy-ai.vercel.app` in `CORS_ORIGINS`.

2. **Storage Subsystem Observability:**
   - **Commit `03a1793` Status:** Live adapter implemented.
   - **Live Health Status:** `/api/health` and `/api/v1/storage/status` return `200 OK` with observable provider tracking.
   - **Activation Dependency:** The Render dashboard must have the 5 environment variables configured (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME=project9`, `R2_ENDPOINT`). Until saved in Render Dashboard, backend uses local storage fallback gracefully.

3. **Authentication & Multi-Tenant Ownership Model:**
   - **Finding:** There is currently no `users` table or auth router in the backend codebase. The application operates as a single-tenant scientific reliability lab.
   - **Architectural Impact:** There are no broken foreign keys to non-existent user tables. However, multi-user isolation (Clerk/Supabase Auth) requires adding user ownership foreign keys (`user_id`) to `datasets` and `experiments` tables if multi-user isolation is desired. For current single-tenant deployment, endpoints are public within CORS boundaries.

---

### 2.3 Database Subsystem (Supabase PostgreSQL)

- **Connection State:** Fully operational via asyncpg with SSL (`aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres`).
- **Alembic Version:** `001_initial_tables` (Verified current).
- **Canonical Table Inventory:**
  - `alembic_version`: 1 row
  - `artifact_manifests`: 269 rows
  - `artifact_references`: 0 rows (New storage subsystem ready to populate on subsequent runs)
  - `datasets`: 2 benchmark rows (`iris`, `german-credit`)
  - `experiment_results`: 8 rows
  - `experiment_runs`: 45 rows
  - `experiments`: 9 rows (EXP-0001 through EXP-0009)
  - `failed_samples`: 120 rows
  - `model_adapters`: 4 rows (`random_forest`, `logistic_regression`, `gradient_boosting`, `mlp`)
- **Foreign Key Invariants:** All existing runs and results reference valid experiments. CASCADE deletion is configured properly.

---

### 2.4 Cloudflare R2 Object Storage

- **Bucket Name:** `project9`
- **Account ID:** `916b7f70128acc095b09c70a1c1d6318`
- **Live Endpoint Verification:** Verified via live probe (`head_bucket`, `put_object`, `get_object`, `generate_presigned_url`, and `delete_object` all succeeded with HTTP 200).
- **Integrity:** SHA-256 validation enforced on uploads and atomic download staging prevents corrupted reads.

---

### 2.5 ML Engine Subsystem (`ml_engine/`)

- **Test Suite Status:** 116 / 116 unit and protocol tests passing.
- **Execution Script Inventory:** `scripts/experiments/run_e001.py` through `run_e006.py`.
- **Subprocess Integration:** Managed via `ml_engine_bridge.py`.
- **Dataset Loading:** Uses canonical dataset loaders for Iris and German Credit; custom datasets load via `data/datasets/{dataset_id}/data.csv` or R2 staged local download.

---

## 3. Prioritized Integration Defect Matrix

| Priority | Issue ID | Component | Defect Description | Planned Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **P0** | DEF-001 | Frontend | `NEXT_PUBLIC_USE_MOCKS !== 'false'` forces client mock mode in production | Invert logic: default to `false` (live API), only use mocks when `NEXT_PUBLIC_USE_MOCKS === 'true'` |
| **P0** | DEF-002 | Frontend | `next.config.js` rewrites fallback to `http://127.0.0.1:8000` | Fallback to `https://model-autopsy-backend.onrender.com` in production |
| **P0** | DEF-003 | Frontend | `Step1Dataset.tsx` simulates CSV upload via `setTimeout` and fake schema | Connect to `POST /api/v1/datasets/upload` using `FormData` |
| **P1** | DEF-004 | Frontend | `app/api/experiments/e003/route.ts` shadows backend and checks missing disk file | Route to backend API or remove shadow route so rewrite proxies cleanly |
| **P1** | DEF-005 | Frontend | `useRunStatus.ts` simulates progress via timer without polling real backend | Implement 2.5s polling loop querying `GET /api/experiments/{id}` |
| **P1** | DEF-006 | Frontend | `results/page.tsx` & `report/page.tsx` silently substitute `HERO_EXPERIMENT` | Display real experiment data; show appropriate loading/error state if results are missing |
| **P1** | DEF-007 | Frontend | `reports/page.tsx` hardcoded to filter `MOCK_EXPERIMENTS` | Fetch real completed experiments from `api.getExperiments()` |
| **P2** | DEF-008 | Backend | `CORS_ORIGINS` missing explicit production domain | Add `https://model-autopsy-ai.vercel.app` to explicit CORS list |
| **P2** | DEF-009 | Frontend | Missing dataset CSV download button on dataset detail page | Add direct download action pointing to `/api/v1/datasets/{id}/download` |
| **P2** | DEF-010 | Frontend | Artifact downloads in report export stringify local JSON instead of downloading real R2 artifacts | Wire download buttons to `/api/v1/experiments/{id}/artifacts/{results.json, curves.csv, report.md}` |

---

## 4. Remediation Plan

1. **Phase 2 Execution:**
   - Patch `frontend/lib/api.ts` to disable mock mode by default and support real dataset upload.
   - Patch `frontend/next.config.js` to ensure production proxy always routes to Render.
   - Remove/update `frontend/app/api/experiments/e003/route.ts`.
   - Update `Step1Dataset.tsx` to perform real CSV upload.
   - Update `useRunStatus.ts` to poll real backend progress.
   - Update `results/page.tsx`, `report/page.tsx`, and `reports/page.tsx` to remove mock fallbacks and wire real artifact downloads.
   - Add explicit Vercel URL to backend CORS origins.
2. **Phase 3 & 4 Verification:**
   - Execute end-to-end dataset upload through the live API.
   - Verify Supabase record and Cloudflare R2 object creation.
3. **Phase 5 & 6 End-to-End Validation:**
   - Run a real experiment against the live backend and verify progression from queued $\rightarrow$ running $\rightarrow$ completed.
   - Verify artifact replication into Cloudflare R2 and download integrity.

