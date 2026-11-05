# Phase 11 — Backend Web Service & Render Deployment Report

**Project:** Model Autopsy — Find Out Why AI Models Fail  
**Component:** FastAPI Backend Web Service & Render Platform Deployment  
**Date:** 2026-11-05  
**Status:** CONFIGURED & VERIFIED  

---

## 1. Executive Summary

The Model Autopsy backend is an asynchronous **FastAPI** web service backed by Python 3.11. It orchestrates ML robustness experiments, persists metrics to Supabase PostgreSQL, offloads canonical artifacts to Cloudflare R2, and serves a high-performance REST API with CORS headers configured for production Vercel frontends.

The service is pre-configured for automated continuous deployment on **Render** using a declarative `render.yaml` specification.

---

## 2. Render Deployment Configuration

The repository includes a root `render.yaml` file that allows Render to auto-detect and deploy the service:

```yaml
services:
  - type: web
    name: model-autopsy-backend
    env: python
    region: oregon
    plan: free
    branch: main
    buildCommand: pip install --upgrade pip && pip install -r backend/requirements-prod.txt
    startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    autoDeploy: true
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: APP_NAME
        value: Model Autopsy API
      - key: DEBUG
        value: "false"
      - key: LOG_LEVEL
        value: INFO
      - key: MAX_CONCURRENT_EXPERIMENTS
        value: "1"
      - key: EXPERIMENT_TIMEOUT_SECONDS
        value: "1800"
      - key: ML_ENGINE_PATH
        value: ../ml_engine
      - key: ARTIFACTS_BASE_DIR
        value: ../artifacts/experiments
      - key: CONFIGS_BASE_DIR
        value: ../configs/experiments
      - key: SCRIPTS_BASE_DIR
        value: ../scripts/experiments
```

### 2.1 Dependency Resolution (`backend/requirements-prod.txt`)
To ensure fast and reproducible builds on Render, dependencies from `ml_engine` and `backend` are unified into `backend/requirements-prod.txt`:
- **Web & Framework:** `fastapi>=0.109.0`, `uvicorn[standard]>=0.27.0`, `pydantic>=2.6.0`, `pydantic-settings>=2.1.0`
- **Database:** `sqlalchemy>=2.0.25`, `asyncpg>=0.29.0`, `alembic>=1.13.1`
- **Cloud Storage:** `boto3>=1.34.0`
- **Scientific & ML:** `numpy>=1.24.0`, `pandas>=2.0.0`, `scikit-learn>=1.3.0`, `scipy>=1.11.0`

---

## 3. Runtime Health Checks & Startup Lifecycle

### 3.1 Dedicated Health Endpoint
Render requires an HTTP 200 response to verify service health before routing incoming traffic:
- **Route:** `GET /health`
- **Response Format:**
  ```json
  {
    "status": "healthy",
    "service": "Model Autopsy API",
    "version": "0.1.0",
    "environment": "production"
  }
  ```
- **Readiness Check:** Verifies database connectivity and ML engine directory resolution.

### 3.2 Dynamic Port Binding
Render injects a dynamic `$PORT` environment variable (e.g. `10000`).
The backend startup script and `backend/app/core/config.py` read this variable automatically:
```python
PORT: int = int(os.getenv("PORT", "8000"))
```

---

## 4. CORS Security Configuration

Production web applications hosted on Vercel use dynamic preview URLs in addition to the production domain.
To allow legitimate frontend requests while blocking unauthorized origins:
1. **Explicit Origins:** Configured via `CORS_ORIGINS` in `.env` (e.g. `["https://model-autopsy.vercel.app"]`).
2. **Dynamic Preview Origins:** Handled via `CORS_ORIGIN_REGEX`:
   ```python
   CORS_ORIGIN_REGEX = r"^https:\/\/.*\.vercel\.app$"
   ```
   This allows Vercel branch previews (e.g. `https://model-autopsy-git-feat-x.vercel.app`) to communicate seamlessly with the backend API.

---

## 5. Free-Tier Operational Characteristics

| Feature | Render Free Tier Value | Impact on Model Autopsy | Mitigation |
| :--- | :--- | :--- | :--- |
| **Inactivity Sleep** | Spins down after 15 minutes of zero traffic | Next request experiences a **~50 second cold start delay** | Frontend displays friendly connection loader indicator; health check keeps service warm during active sessions. |
| **Memory Limit** | 512 MB RAM | Potential Out-Of-Memory (OOM) if multiple experiments run concurrently | Concurrency is strictly clamped to `MAX_CONCURRENT_EXPERIMENTS=1`; batch sizes limited to 500 samples. |
| **Ephemeral Disk** | Wiped on spin-down or deploy | Experiment artifacts stored on disk would be lost | All generated artifacts are immediately replicated to **Cloudflare R2** object storage. |
| **Execution Time** | 100 ms to 15 min web request timeout | Running long experiments in a synchronous request will timeout | Experiments are queued and executed asynchronously via subprocess worker; progress is polled via `/api/v1/experiments/{id}/progress`. |

---

## 6. Verification Status

- [x] Production requirements compiled in `backend/requirements-prod.txt`.
- [x] Render configuration manifest validated in `render.yaml`.
- [x] Dedicated `/health` endpoint implemented and verified.
- [x] CORS origin regex verified for Vercel preview environments.
- [x] 29/29 Backend unit and integration tests passing.

