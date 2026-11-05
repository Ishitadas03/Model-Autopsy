# Model Autopsy — Phase 11 Initial Repository & Infrastructure Audit

**Audit Date:** 2026-11-05  
**Auditor:** Principal DevOps Engineer & Cloud Architect  
**Repository:** `https://github.com/Ishitadas03/Model-Autopsy.git`  
**Current Branch:** `main`  
**Target Infrastructure:** Vercel (Frontend Next.js 14), Render (FastAPI Backend + ML Engine), Supabase (PostgreSQL 16), Cloudflare R2 (S3-compatible Object Storage).

---

## 1. Executive Summary

This independent audit assesses the complete Model Autopsy monorepo prior to cloud deployment. The repository houses a full-stack scientific application designed to stress-test machine learning models, identify empirical failure boundaries, compute area-under-degradation curves (AUDC), and generate reproducible diagnostic reports.

All 185 tests across the ML Engine, Backend API, and Frontend have been independently re-run and verified passing (116/116 ML Engine, 29/29 Backend, 40/40 Frontend).

---

## 2. Monorepo Architecture & Component Inventory

```
Model-Autopsy/
├── artifacts/experiments/        # Canonical research artifacts (E001-E006)
│   ├── E001/ ... E006/           # JSON aggregates, curves.csv, report.md
├── backend/                      # FastAPI 0.110.0 ASGI application
│   ├── alembic/                  # Database migration scripts (001_initial_tables)
│   ├── app/
│   │   ├── api/v1/endpoints/     # REST routes (experiments, models, datasets, artifacts)
│   │   ├── core/                 # Config (pydantic-settings), database (asyncpg/SQLite), logging
│   │   ├── models/               # 8 SQLAlchemy 2.0 ORM entities
│   │   ├── repositories/         # Async data access repositories
│   │   ├── schemas/              # Pydantic v2 schemas mirroring ML engine contracts
│   │   └── services/             # Artifact, experiment, ML engine bridge, storage service
│   ├── requirements.txt          # Development dependencies
│   ├── requirements-prod.txt     # Production dependencies (Render / Linux)
│   └── tests/                    # 29 Pytest integration & unit tests
├── configs/experiments/          # Experiment YAML specifications (E001-E006)
├── docs/                         # Architecture, deployment, and research documentation
│   ├── deployment/               # Phase 11 production deployment reports
│   └── research/                 # Phase 9 E2E acceptance report & research protocol
├── frontend/                     # Next.js 14 App Router (React 18, Tailwind CSS, Framer Motion)
│   ├── app/                      # App router pages (/workspace, /experiments, /docs, etc.)
│   ├── components/               # UI components, landing hero, charts, telemetry
│   ├── lib/                      # Motion primitives, API client, types
│   ├── public/assets/            # 3D brain assets, videos, textures
│   ├── package.json              # Next.js 14.2.15, Vitest, Lucide
│   └── tests/                    # 40 Vitest unit & component tests
├── ml_engine/                    # Core Python scientific engine (setuptools package `model-autopsy`)
│   ├── src/model_autopsy/
│   │   ├── analysis/             # Boundary detection, failure patterns, statistical tests
│   │   ├── datasets/             # Iris & synthetic dataset loaders with strict split isolation
│   │   ├── metrics/              # Macro-F1, accuracy, confusion matrix, degradation
│   │   ├── models/               # Model adapters (Random Forest, Logistic Regression, etc.)
│   │   ├── schemas/              # Canonical Pydantic v2 schemas
│   │   └── stress_tests/         # Covariate shift, missingness, noise perturbations
│   └── tests/                    # 116 Pytest scientific integrity tests
├── scripts/experiments/          # Experiment execution runners (run_e001.py to run_e006.py)
├── pyproject.toml                # Root build system & package declaration
└── render.yaml                   # Infrastructure-as-Code for Render backend deployment
```

---

## 3. Dependency & Version Analysis

| Component | Target Version | Status | Notes |
|:---|:---|:---|:---|
| **Python** | 3.11.x - 3.13.x | Verified | Tested on Python 3.13.5; Render pinned to 3.11.9 |
| **FastAPI** | 0.110.0 | Verified | Strict Pydantic v2 serialization |
| **SQLAlchemy** | 2.0.30 | Verified | Full async ORM with `asyncpg` and `aiosqlite` |
| **Alembic** | 1.11.1 | Verified | Async migration support configured |
| **Boto3** | 1.34.80+ | Configured | S3-compatible Cloudflare R2 object storage |
| **Next.js** | 14.2.15 | Verified | App Router with standalone/Vercel support |
| **Node.js** | 18.x - 20.x | Verified | Compatible with Vercel deployment |
| **Tailwind CSS** | 3.4.1 | Verified | Full utility generation verified (87KB bundle) |

---

## 4. API Endpoints & Contract Verification

All required REST routes are mounted under `/api` and `/api/v1`:

1. `GET /health` and `GET /api/v1/health`: Liveness & health probe.
2. `GET /api/v1/experiments`: Catalog listing with filtering, sorting, and pagination.
3. `GET /api/v1/experiments/{id}`: Detailed specification, metrics, and failure boundaries.
4. `POST /api/v1/experiments/run`: Async execution trigger for E001–E006.
5. `POST /api/v1/experiments/{id}/cancel`: Subprocess termination and status transition.
6. `GET /api/v1/experiments/{id}/artifacts/{artifact_type}`: Direct artifact streaming or R2 presigned URL redirect.
7. `GET /api/v1/experiments/E003/artifacts/{format}`: Canonical historical E003 artifact benchmark serving.
8. `GET /api/v1/models`: Model adapter registry.
9. `GET /api/v1/datasets`: Benchmark dataset catalog.

---

## 5. Security & Secret Exposure Scan

1. **Git Tracking:**
   - `.env`, `.env.local`, and backend `.env` are strictly excluded in `.gitignore`.
   - No secret API keys or private tokens are tracked in git history.
2. **Database:**
   - Database credentials are read dynamically via `DATABASE_URL` environment variable.
   - SSL encryption (`ssl=require`) is enforced for all remote PostgreSQL endpoints (Supabase).
3. **CORS:**
   - CORS is restricted to `http://localhost:3000` and dynamic regex `^https://.*\.vercel\.app$`.
4. **Filesystem:**
   - Path traversal prevention (`is_relative_to`) is enforced on all artifact endpoints.
   - Executable extensions are forbidden (`.json`, `.csv`, `.png`, `.md`, `.txt` allowed).

---

## 6. Pre-Deployment Test Verification Summary

```
Total Tests Re-verified: 185
------------------------------------
ML Engine Test Suite:  116 / 116 PASS (39.96s)
Backend Test Suite:     29 /  29 PASS (8.33s)
Frontend Test Suite:    40 /  40 PASS (4.15s)
Status:                 100% GREEN
```

