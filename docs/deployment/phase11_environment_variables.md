# Phase 11 — Production Environment Variables Catalog

**Project:** Model Autopsy — Find Out Why AI Models Fail  
**Component:** Production Environment Configuration Matrix  
**Date:** 2026-11-05  

---

## 1. Overview

This document catalogs every environment variable required for production deployment across **Vercel** (Frontend) and **Render** (Backend), along with database settings for **Supabase PostgreSQL** and object storage settings for **Cloudflare R2**.

---

## 2. Frontend Environment Variables (Vercel)

Set these in the **Vercel Dashboard** under **Project Settings > Environment Variables**:

| Variable Name | Required? | Example / Recommended Value | Description |
| :--- | :--- | :--- | :--- |
| `BACKEND_API_URL` | **Yes** | `https://model-autopsy-backend.onrender.com` | Live Render backend URL for API proxying |
| `NEXT_PUBLIC_APP_NAME` | No | `Model Autopsy` | Application display title |
| `NEXT_PUBLIC_USE_MOCKS` | **Yes** | `false` | Set to `false` to consume live backend API data |
| `NEXT_PUBLIC_APP_VERSION`| No | `0.1.0` | Frontend version tag |

---

## 3. Backend Environment Variables (Render)

Set these in the **Render Dashboard** under **Service Settings > Environment Variables**:

### 3.1 Application & Runtime
| Variable Name | Required? | Recommended Value | Description |
| :--- | :--- | :--- | :--- |
| `APP_NAME` | No | `Model Autopsy API` | FastAPI title |
| `APP_VERSION` | No | `0.1.0` | API version |
| `DEBUG` | **Yes** | `false` | Disable debug mode in production |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity (`INFO`, `WARNING`, `ERROR`) |
| `PORT` | Auto | *(Injected by Render)* | Web server bind port (e.g. 10000) |

### 3.2 Database (Supabase PostgreSQL)
| Variable Name | Required? | Example Value | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | **Yes** | `postgresql+asyncpg://postgres:[PASS]@[HOST]:6543/postgres` | Supabase Transaction Pooler connection string |
| `DATABASE_POOL_SIZE` | No | `5` | Active connection pool limit (fit within pooler) |
| `DATABASE_MAX_OVERFLOW` | No | `10` | Temporary burst connection limit |
| `DATABASE_POOL_TIMEOUT` | No | `30` | Connection checkout timeout in seconds |

> [!NOTE]
> If connecting to Supabase, ensure the URL uses `postgresql+asyncpg://` and port `6543` (transaction pooler) or port `5432` (session pooler).

### 3.3 CORS Configuration
| Variable Name | Required? | Example Value | Description |
| :--- | :--- | :--- | :--- |
| `CORS_ORIGINS` | **Yes** | `["https://model-autopsy.vercel.app"]` | Production Vercel domain |
| `CORS_ORIGIN_REGEX` | No | `^https:\/\/.*\.vercel\.app$` | Matches all Vercel branch preview deployments |

### 3.4 Object Storage (Cloudflare R2)
| Variable Name | Required? | Example Value | Description |
| :--- | :--- | :--- | :--- |
| `R2_ACCOUNT_ID` | **Yes** | `a1b2c3d4e5f6...` | Cloudflare Account ID from dashboard |
| `R2_ACCESS_KEY_ID` | **Yes** | `8f9a2b...` | R2 API Token Access Key |
| `R2_SECRET_ACCESS_KEY` | **Yes** | `1a2b3c4d5e...` | R2 API Token Secret Key |
| `R2_BUCKET_NAME` | **Yes** | `model-autopsy-artifacts` | Dedicated R2 bucket name |
| `R2_ENDPOINT_URL` | Auto | `https://<R2_ACCOUNT_ID>.r2.cloudflarestorage.com` | Derived automatically if `R2_ACCOUNT_ID` is set |

### 3.5 ML Engine & Execution Limits
| Variable Name | Required? | Recommended Value | Description |
| :--- | :--- | :--- | :--- |
| `MAX_CONCURRENT_EXPERIMENTS` | **Yes** | `1` | Strictly clamped to 1 for 512MB RAM budget |
| `EXPERIMENT_TIMEOUT_SECONDS` | No | `1800` | Subprocess timeout limit (30 minutes) |
| `DEFAULT_SEEDS` | No | `[42, 123, 456]` | Standard perturbation seeds |
| `ML_ENGINE_PATH` | No | `../ml_engine` | Path to ML engine modules |
| `ARTIFACTS_BASE_DIR` | No | `../artifacts/experiments` | Local artifact spool directory |
| `CONFIGS_BASE_DIR` | No | `../configs/experiments` | Experiment YAML configuration path |
| `SCRIPTS_BASE_DIR` | No | `../scripts/experiments` | Experiment execution script runner path |

---

## 4. Security Practices

1. Never commit `.env` files with production values to GitHub.
2. Use platform environment secret storage with encrypted at-rest protection.
3. Rotate R2 access keys every 90 days.
4. Keep the database password separate from the application API keys.

