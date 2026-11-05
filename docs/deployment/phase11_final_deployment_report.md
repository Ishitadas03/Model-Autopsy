# Phase 11 — Final End-to-End Cloud Deployment & Verification Report

**Project:** Model Autopsy — Find Out Why AI Models Fail  
**Repository:** `https://github.com/Ishitadas03/Model-Autopsy.git`  
**Phase:** 11 — Production Deployment, Cloud Infrastructure & Live Verification  
**Auditor / Engineer:** Principal DevOps & Cloud Infrastructure Specialist  
**Date:** 2026-11-05  
**Final Acceptance Verdict:** **READY FOR CLOUD DASHBOARD CONNECTION (ALL CODEBASE PREREQUISITES VERIFIED)**

---

## 1. Executive Summary & Verification Highlights

Model Autopsy has been engineered and prepared for free-tier cloud deployment across the following architecture:
- **Frontend:** Next.js 14 on **Vercel** (`frontend/vercel.json`, `next.config.js` proxy).
- **Backend:** FastAPI on **Render** (`render.yaml`, `backend/requirements-prod.txt`, `/health` probe).
- **Database:** PostgreSQL on **Supabase** (SQLAlchemy 2.0, PgBouncer pooler port 6543, SSL require).
- **Object Storage:** S3-compatible **Cloudflare R2** (`backend/app/services/storage_service.py`, presigned URLs, zero egress fees).

### Verification Evidence
1. **Total Test Suite:** **185 tests passing out of 185** (100% pass rate).
   - **ML Engine:** 116 passed (`python -m pytest ml_engine/tests/`)
   - **Backend:** 29 passed (`python -m pytest backend/tests/`)
   - **Frontend:** 40 passed (`node node_modules/vitest/vitest.mjs run`)
2. **UI Glitch Resolved:** The oversized ECG waveform issue on `localhost:3000` was traced to unconstrained SVG rendering before CSS stylesheet hydration. Fixed permanently in `frontend/components/ui/Logo.tsx` with explicit `width` and `height` properties.
3. **Artifact Persistence:** Render free-tier ephemeral disk risk solved with automatic Cloudflare R2 object storage upload and presigned 307 redirect fallbacks.

---

## 2. Cloud Architecture Diagram

```
+-----------------------------------------------------------------------------------------+
|                               MODEL AUTOPSY CLOUD TOPOLOGY                              |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|       USER BROWSER / CLIENT                                                             |
|                 │                                                                       |
|                 ▼                                                                       |
|   +───────────────────────────+                                                         |
|   |          VERCEL           |                                                         |
|   |    Next.js 14 Frontend    |                                                         |
|   |  (React, Tailwind, SVG)   |                                                         |
|   +─────────────┬─────────────+                                                         |
|                 │                                                                       |
|                 │ /api/v1/* (Next.js Rewrite Proxy)                                     |
|                 ▼                                                                       |
|   +───────────────────────────+                                                         |
|   |          RENDER           |                                                         |
|   |   FastAPI Python 3.11     |                                                         |
|   |   Subprocess ML Runner    |                                                         |
|   |   (Health Check: /health) |                                                         |
|   +───────┬───────────┬───────+                                                         |
|           │           │                                                                 |
|           │           │                                                                 |
|    SQLAlchemy 2.0     │ S3-Compatible API                                               |
|    (SSL / Port 6543)  │ (Presigned URLs / 0 Egress)                                     |
|           │           │                                                                 |
|           ▼           ▼                                                                 |
|   +───────────────+ +───────────────────+                                               |
|   |   SUPABASE    | |   CLOUDFLARE R2   |                                               |
|   |  PostgreSQL   | |  Object Storage   |                                               |
|   |  (8 Tables)   | | (JSON, CSV, MD)   |                                               |
|   +───────────────+ +───────────────────+                                               |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Step-by-Step Cloud Dashboard Setup Runbook

Because production platform dashboards (Render, Vercel, Supabase, Cloudflare) require personal owner authentication via browser OAuth, follow these straightforward steps to connect your repository:

### Step 1: Push Local Updates to GitHub
Before connecting the cloud dashboards, ensure the latest deployment manifests are pushed to GitHub:
```bash
git add .
git commit -m "feat(deployment): configure Render, Vercel, Supabase, and Cloudflare R2 for Phase 11"
git push origin main
```

---

### Step 2: Set Up Supabase Database (Free Tier)
1. Log in to [Supabase](https://supabase.com).
2. Click **New Project** and name it `model-autopsy`.
3. Set a strong database password (keep this secure).
4. Once provisioned, navigate to **Project Settings > Database**.
5. Under **Connection string > URI**, copy the connection string.
6. Select **Transaction Pooler** (Port `6543`) or Session Pooler (Port `5432`).
7. Prefix the protocol with `postgresql+asyncpg://` instead of `postgresql://`:
   ```
   postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

---

### Step 3: Set Up Cloudflare R2 Object Storage (Free Tier)
1. Log in to the [Cloudflare Dashboard](https://dash.cloudflare.com) and navigate to **R2**.
2. Click **Create Bucket**, name it `model-autopsy-artifacts`, and keep it private.
3. On the R2 overview page, note your **Account ID** (visible on the right sidebar).
4. Click **Manage R2 API Tokens > Create API Token**:
   - Permission: **Object Read & Write**
   - Bucket: Apply to `model-autopsy-artifacts`
5. Copy the generated **Access Key ID** and **Secret Access Key**.

---

### Step 4: Deploy Backend on Render (Free Tier)
1. Log in to [Render](https://render.com).
2. Click **New + > Blueprint** (or **Web Service**).
3. Connect your GitHub repository: `https://github.com/Ishitadas03/Model-Autopsy`.
4. Render will detect `render.yaml` automatically!
5. In the **Environment Variables** section, populate the following sensitive variables:
   - `DATABASE_URL`: Your Supabase connection string from Step 2.
   - `R2_ACCOUNT_ID`: Your Cloudflare Account ID from Step 3.
   - `R2_ACCESS_KEY_ID`: Your R2 Access Key ID.
   - `R2_SECRET_ACCESS_KEY`: Your R2 Secret Access Key.
   - `R2_BUCKET_NAME`: `model-autopsy-artifacts`
   - `CORS_ORIGINS`: `["https://model-autopsy.vercel.app"]` (or your initial domain).
6. Click **Apply / Create Web Service**.
7. Render will build using `backend/requirements-prod.txt` and launch with Uvicorn. Once active, note the assigned URL (e.g., `https://model-autopsy-backend.onrender.com`).

---

### Step 5: Deploy Frontend on Vercel (Free Tier)
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New... > Project**.
3. Import your GitHub repository: `Ishitadas03/Model-Autopsy`.
4. Set the **Root Directory** to `frontend`.
5. Under **Environment Variables**, configure:
   - `BACKEND_API_URL`: Your Render backend URL (e.g. `https://model-autopsy-backend.onrender.com`).
   - `NEXT_PUBLIC_USE_MOCKS`: `false`
6. Click **Deploy**.
7. Vercel will build Next.js 14 in ~60 seconds and assign a live production URL (e.g., `https://model-autopsy.vercel.app`).

---

## 4. Free-Tier Operational Characteristics

| Service | Plan | Limitations | Applied Mitigation in Model Autopsy |
| :--- | :--- | :--- | :--- |
| **Vercel** | Hobby (Free) | 100 GB bandwidth / mo | Static caching, SVG sizing hardening |
| **Render** | Free Web Service | Sleep after 15m inactivity, 50s cold start, 512MB RAM | Client waking state indicator, `MAX_CONCURRENT_EXPERIMENTS=1`, subprocess memory reclamation |
| **Supabase** | Free Tier | 500 MB DB storage, auto-pause after 7 days inactivity | Artifacts stored in R2 (PostgreSQL stores <10MB metadata), 1-click unpause runbook |
| **Cloudflare R2**| Free Tier | 10 GB storage, 1M Class A ops, 10M Class B ops | Zero egress fees, signed URLs with 1h TTL |

---

## 5. Acceptance Deliverables Catalog

All required Phase 11 documentation has been created in `docs/deployment/`:
- `phase11_initial_audit.md` — Complete repository inventory and dependency assessment.
- `phase11_database_report.md` — Supabase PostgreSQL schema, connection pooling, and SSL guide.
- `phase11_storage_report.md` — Cloudflare R2 S3-compatible architecture and signed URLs.
- `phase11_backend_report.md` — Render FastAPI deployment, health check, and dynamic port binding.
- `phase11_ml_execution_report.md` — Subprocess lifecycle and memory budget profiling.
- `phase11_frontend_report.md` — Vercel Next.js 14 setup and UI SVG scaling fix.
- `phase11_security_report.md` — Path traversal, CORS regex, and secret isolation audit.
- `phase11_environment_variables.md` — Production environment variable matrix.
- `phase11_troubleshooting.md` — Runbooks for cold starts, inactivity pauses, and OOM prevention.
- `phase11_deployment_evidence.json` — Machine-readable test status and configuration parameters.
- `phase11_final_deployment_report.md` — This comprehensive verdict and setup guide.

---

## 6. Official Verdict

**VERDICT:** **READY FOR CLOUD DASHBOARD CONNECTION**  
The Model Autopsy repository is fully prepared, tested (185/185 passing), hardened against UI glitches, and ready for deployment.

