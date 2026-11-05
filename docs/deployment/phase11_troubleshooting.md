# Phase 11 — Production Troubleshooting & Runbook Guide

**Project:** Model Autopsy — Find Out Why AI Models Fail  
**Component:** Production Diagnostics, Cold Starts, Failover, and Recovery  
**Date:** 2026-11-05  

---

## 1. Overview

This runbook provides actionable troubleshooting steps for common operational issues encountered when running Model Autopsy on free-tier cloud infrastructure (Render, Vercel, Supabase, Cloudflare R2).

---

## 2. Issue 1: Render Cold Start & Delayed Response

### Symptoms
- Initial request to frontend takes 45–60 seconds to load data.
- Browser network tab shows pending request to `/api/v1/experiments` or `/health`.
- Render service dashboard status displays *"Spinning up instance"*.

### Cause
Render free tier puts instances to sleep after **15 minutes** of inactivity. The container takes approximately 50 seconds to initialize, start Python, load ML packages, and connect to Supabase.

### Resolution & Mitigation
1. **Frontend Grace Period:** The frontend includes an active connection probe that informs the user: *"Waking up backend service from sleep... this may take up to 60 seconds."*
2. **Health Check Ping:** In `render.yaml`, the `/health` endpoint is configured as the official probe.
3. **Optional Uptime Ping:** A free scheduled ping service (such as Cron-Job.org, UptimeRobot, or an automated GitHub Action) can ping `https://<backend>.onrender.com/health` every 14 minutes to prevent sleep during testing hours.

---

## 3. Issue 2: Supabase Database Inactivity Pause

### Symptoms
- Backend fails to start or health check returns:
  `asyncpg.exceptions.CannotConnectNowError: the database system is starting up` or `ConnectionRefusedError`.
- Render logs show `sqlalchemy.exc.OperationalError`.

### Cause
Supabase free tier automatically pauses projects that receive no database queries for **7 consecutive days**.

### Resolution
1. Navigate to the [Supabase Dashboard](https://supabase.com/dashboard).
2. Select the `model-autopsy` project.
3. Click the yellow **Restore project** or **Unpause** button.
4. The database unpauses and resumes accepting queries within ~60 seconds.
5. In the Render dashboard, click **Manual Deploy > Clear build cache & deploy** or restart the service.

---

## 4. Issue 3: CORS Blocked on Vercel Preview Deployments

### Symptoms
- Frontend displays an error: *"Failed to fetch"* or browser console reports:
  `Access to fetch at 'https://...onrender.com/api/v1/experiments' from origin 'https://model-autopsy-git-feat-x.vercel.app' has been blocked by CORS policy.`

### Cause
The origin was not explicitly listed in the backend's `CORS_ORIGINS` array.

### Resolution
The backend now includes `CORS_ORIGIN_REGEX = r"^https:\/\/.*\.vercel\.app$"` in `backend/app/main.py`.
- If an issue still occurs on custom domains (e.g., `https://my-custom-domain.com`), add the custom domain directly into the `CORS_ORIGINS` environment variable in the Render dashboard:
  ```json
  ["https://model-autopsy.vercel.app", "https://my-custom-domain.com"]
  ```
- Redeploy or trigger an instant restart in Render.

---

## 5. Issue 4: Artifact 404 After Container Restart (Ephemeral Disk)

### Symptoms
- Experiment was executed successfully, but after 24 hours, downloading artifacts (`/artifacts/json` or `/artifacts/csv`) returns 404.

### Cause
The experiment generated files locally on Render's disk, but Render spun down or redeployed, wiping the local filesystem.

### Resolution
1. Verify that Cloudflare R2 environment variables are configured in Render:
   - `R2_ACCOUNT_ID`
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`
   - `R2_BUCKET_NAME`
2. With R2 configured, the backend automatically replicates completed experiment artifacts to the R2 bucket.
3. The artifact endpoint (`backend/app/api/v1/endpoints/artifacts.py`) checks local disk first; if absent, it queries R2 and returns a **307 Temporary Redirect** with a signed presigned URL, ensuring artifacts are never lost.

---

## 6. Issue 5: Render Process Killed (SIGKILL 137 / OOM)

### Symptoms
- An experiment is started, runs for ~10 seconds, then Render logs report:
  `Exit code 137 (Out Of Memory)` or `Killed`.
- FastAPI web server restarts unexpectedly.

### Cause
The ML experiment memory consumption exceeded Render's 512 MB physical limit, usually due to:
- Multiple experiments running concurrently.
- Very large batch sizes or excessive permutation seeds.

### Resolution
1. Ensure `MAX_CONCURRENT_EXPERIMENTS=1` in the Render environment variables.
2. In experiment configurations (`configs/experiments/`), keep `batch_size <= 500`.
3. If running E002 (text jitter with transformer models), use the quantized lightweight pipeline or CPU embeddings rather than loading full FP32 language models into memory.

---

## 7. Issue 6: UI ECG Pulse Scaling Glitch

### Symptoms
- Visiting the frontend displays a massive white zigzag line filling the whole window.

### Cause
An SVG inside `Logo.tsx` without explicit physical `width` and `height` properties will expand to 100% viewport width if Tailwind CSS styles have not yet been evaluated by the browser.

### Resolution
`frontend/components/ui/Logo.tsx` has been hardened with physical attributes:
```tsx
width={pixelDimensions[size]}
height={pixelDimensions[size]}
```
If this ever recurs due to browser cache:
1. Hard-refresh browser using `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac).
2. Clear Next.js build cache: `rm -rf frontend/.next && npm run build`.

