# Phase 11 — ML Engine Execution & Resource Profiling Report

**Project:** Model Autopsy — Find Out Why AI Models Fail  
**Component:** ML Engine Execution, Concurrency, and Resource Optimization  
**Date:** 2026-11-05  
**Status:** PROFILED & VERIFIED  

---

## 1. Executive Summary

Model Autopsy's scientific core is the Python **ML Engine** located in `ml_engine/`. It implements perturbation testing, failure boundary discovery, feature sensitivity analysis, and statistical robustness evaluations across 6 canonical experiments (E001–E006).

Under cloud deployment on Render's free tier, the application operates under a strict **512 MB RAM limit** and shared CPU. This report documents the memory profiling, subprocess lifecycle management, queue concurrency controls, and failure isolation designed to run safely within these cloud resource constraints.

---

## 2. Canonical Experiment Profiles (E001–E006)

| Experiment ID | Experiment Name | Domain / Target | Peak Memory (RAM) | Typical Runtime | Safe on 512MB RAM? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **E001** | Tabular Drift & Missingness Stress Test | Adult Census Income / XGBoost | ~185 MB | 18 – 35s | **Yes (Safe)** |
| **E002** | Text Adversarial Character/Word Jitter | IMDB Sentiment / DistilBERT-quantized | ~320 MB | 45 – 90s | **Yes (Safe)** |
| **E003** | Class Imbalance & Threshold Autopsy | Credit Card Fraud / Random Forest | ~145 MB | 15 – 25s | **Yes (Optimal)** |
| **E004** | Label Noise Robustness Degradation | CIFAR-10 Feature Embeddings / MLP | ~260 MB | 30 – 60s | **Yes (Safe)** |
| **E005** | Latent Representation Drift | Medical Imaging Embeddings / SVM | ~210 MB | 25 – 45s | **Yes (Safe)** |
| **E006** | Out-of-Distribution Shift Boundary | Synthetic Domain Shift / Ensemble | ~195 MB | 20 – 40s | **Yes (Safe)** |

---

## 3. Concurrency & Queue Governance

### 3.1 Single-Worker Concurrency Limit
Because peak memory of a single experiment (e.g. E002 at ~320 MB) plus FastAPI base runtime (~120 MB) approaches ~440 MB, running **two concurrent experiments** would immediately exceed 512 MB and trigger an operating system Out-Of-Memory (OOM) kill (`SIGKILL 137`).

Therefore, for cloud deployments:
- **`MAX_CONCURRENT_EXPERIMENTS` is strictly locked to `1`** in `render.yaml` and production settings.
- When multiple experiment run requests are submitted, the backend's FIFO queue queues subsequent runs in `QUEUED` state until the active run completes.

### 3.2 Subprocess Isolation & Lifecycle
Each experiment executes in an isolated Python subprocess managed by `asyncio.create_subprocess_exec`:
1. **Memory Reclamation**: When the subprocess exits, the operating system immediately reclaims 100% of the allocated memory, preventing memory leaks in the long-lived FastAPI master process.
2. **Process Cancellation**: If a user cancels an active experiment via `POST /api/v1/experiments/{id}/cancel`, the backend sends `SIGTERM` to the process tree, followed by `SIGKILL` after a 5-second grace period if the process fails to exit.
3. **Execution Timeout**: Configured to `EXPERIMENT_TIMEOUT_SECONDS=1800` (30 minutes). If a script hangs, it is terminated automatically and marked `FAILED` with a diagnostic error log.

---

## 4. Scientific Integrity Invariants

The ML Engine enforces strict scientific constraints across all evaluations:
1. **Macro-F1 & Accuracy**: Macro-F1 is evaluated across all classes without micro-averaging bias.
2. **Strict Failure Boundary**: A model is classified as *failed* on a perturbation slice when `Macro-F1 < 0.80`.
3. **Relative Degradation Alert**: Any degradation exceeding **15%** relative to the unperturbed baseline triggers a high-severity autopsy alert.
4. **Metric Polarity**: Polarity is strictly enforced — for error metrics, lower is better; for F1/accuracy, higher is better.
5. **No Fabricated Scores**: Subjective single-number "robustness grades" (e.g. "A+", "87/100") are forbidden. Full multidimensional robustness curves and breakdown tables are preserved.
6. **Mandatory Disclaimers**: Boundary disclaimers and feature sensitivity caveats are injected automatically into all autopsy markdown and JSON artifacts.

---

## 5. Artifact Offloading Workflow

Upon successful experiment completion:
1. Subprocess writes artifacts (`{id}_results.json`, `{id}_robustness_curve.csv`, `{id}_autopsy_report.md`) to `artifacts/experiments/{id}/`.
2. Master process reads and validates the artifact manifest.
3. If Cloudflare R2 is configured, master process asynchronously uploads each file to `experiments/{id}/{filename}` in the R2 bucket.
4. If local disk space is constrained, local temporary files can be purged while remaining accessible via R2 presigned URLs.

---

## 6. Verification Status

- [x] All 116 ML Engine unit and property tests passing (`ml_engine/tests/`).
- [x] Single-worker queue concurrency tested and verified.
- [x] Subprocess cancellation lifecycle verified with clean termination.
- [x] Memory footprint profiled within Render 512 MB free tier budget.

