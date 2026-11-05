# Model Autopsy — Person 1 Final Handoff & Backend Integration Specification

**Document ID:** `HANDOFF-PERSON1-TO-PERSON2-20261027`  
**Author:** Person 1 (Principal ML Research Engineer & ML Platform Architect)  
**Target Recipient:** Person 2 (Backend, Platform & Full-Stack Engineer)  
**Repository:** [Model Autopsy (GitHub)](https://github.com/Ishitadas03/Model-Autopsy.git)  
**Historical Syntheses:**
- [`docs/research/master_research_summary.md`](file:///c:/Users/ishit/Model-Autopsy/docs/research/master_research_summary.md)
- [`docs/research/backend_integration_contract.md`](file:///c:/Users/ishit/Model-Autopsy/docs/research/backend_integration_contract.md)  
**Status:** Approved Final Handoff Specification  
**Audit Timestamp:** 2026-10-27 22:45:00 UTC  

---

## 1. Executive Summary & Ownership Boundaries

This handoff document formally concludes **Person 1's** responsibilities (ML Engine, Scientific Research, Pre-registered Experiments E001–E006, Statistical Auditing, and Canonical Pydantic v2 Schemas). It provides **Person 2** with the exact specifications, import paths, runner interfaces, artifact conventions, progress calculation rules, and verification procedures required to build the FastAPI backend service and connect the Next.js frontend.

### Strict Ownership Boundaries
```
+---------------------------------------------------------------------------------------+
| PERSON 1 RESPONSIBILITIES (COMPLETED & SEALED)                                        |
+---------------------------------------------------------------------------------------+
|  ml_engine/src/model_autopsy/       Core ML algorithms, adapters, stress operators     |
|  ml_engine/src/model_autopsy/schemas/ Canonical Pydantic v2 domain & API schemas      |
|  ml_engine/tests/                   116 passing tests (unit, protocol, and schemas)   |
|  configs/experiments/               YAML configs for E001 through E006                 |
|  artifacts/experiments/             Canonical experiment outputs & manifests           |
|  docs/research/                     All designs, scientific audits, and syntheses      |
+---------------------------------------------------------------------------------------+
| PERSON 2 RESPONSIBILITIES (READY FOR IMPLEMENTATION)                                  |
+---------------------------------------------------------------------------------------+
|  backend/app/main.py                FastAPI application factory & lifespan manager     |
|  backend/app/api/v1/                REST API endpoint routers                          |
|  backend/app/services/              Experiment execution worker & artifact service     |
|  backend/tests/                     FastAPI endpoint tests (TestClient)                |
|  frontend/                          Connect Next.js UI to live FastAPI endpoints       |
|                                     (Retire mock EXP-0241 with real experiment data)   |
+---------------------------------------------------------------------------------------+
```

---

## 2. Canonical Schema Ownership & Import Specification

### 2.1 Single Source of Truth
The ML engine owns all API contracts. Do not create duplicate Pydantic models in `backend/app/`.

- **ML Engine Source:** [`ml_engine/src/model_autopsy/schemas/`](file:///c:/Users/ishit/Model-Autopsy/ml_engine/src/model_autopsy/schemas/)
- **Backend Re-Export:** [`backend/app/schemas/__init__.py`](file:///c:/Users/ishit/Model-Autopsy/backend/app/schemas/__init__.py)

In your backend code, you may import from either location identically:
```python
# Preferred in backend routers:
from backend.app.schemas import (
    ExperimentRunRequest,
    ExperimentSummarySchema,
    ExperimentDetailSchema,
    ExperimentProgressSchema,
    ExperimentCancelResponse,
    ApiErrorResponse,
    RunStatus,
    MetricType,
    StressType,
)
```

### 2.2 Dual Wire-Format Serialization (camelCase & snake_case)
Every canonical schema inherits from `SchemaBase` with:
```python
model_config = ConfigDict(
    from_attributes=True,
    populate_by_name=True,
    validate_assignment=True,
    extra="forbid",
)
```
- **From Python Code / Dataclasses:** Pass native Python snake_case keyword arguments or dataclass instances directly via `Schema.model_validate(dataclass_instance)`.
- **From Frontend JSON Requests:** The models automatically accept camelCase keys (`datasetId`, `modelId`, `stressConfig`, `failureThreshold`, `progressPercent`, `createdAt`).
- **To Frontend JSON Responses:** Use `schema.model_dump(by_alias=True)` or return the Pydantic instance directly in FastAPI path operations to automatically emit camelCase keys matching [`frontend/lib/schemas.ts`](file:///c:/Users/ishit/Model-Autopsy/frontend/lib/schemas.ts).

---

## 3. Experiment Runner Invocation Contracts

All six experiment runners are implemented, verified, and exported in `model_autopsy.experiments`:

```python
from model_autopsy.experiments import (
    run_e001_experiment,
    run_e001_multiseed_experiment,
    run_e002_experiment,
    run_e003_experiment,
    run_e004_experiment,
    run_e005_experiment,
    run_e006_experiment,
)
```

### 3.1 Runner Interface Specifications

| Experiment ID | Primary Function | Supported Arguments | Default Output Directory | Approximate Execution Time |
|:---:|---|---|---|:---:|
| **E001** | `run_e001_multiseed_experiment` | `config_path: Optional[Path]`, `seeds: List[int]`, `output_dir: Optional[Path]` | `artifacts/experiments/E001_multi_seed` | $\approx 2\,\text{seconds}$ |
| **E002** | `run_e002_experiment` | `config_path: Optional[Path]`, `seeds: List[int]`, `output_dir: Optional[Path]` | `artifacts/experiments/E002` | $\approx 5\,\text{seconds}$ |
| **E003** | `run_e003_experiment` | `config_path: Optional[Path]`, `seeds: List[int]`, `output_dir: Optional[Path]` | `artifacts/experiments/E003` | $\approx 15\,\text{seconds}$ |
| **E004** | `run_e004_experiment` | `config_path: Optional[Path]`, `seeds: List[int]`, `output_dir: Optional[Path]` | `artifacts/experiments/E004` | $\approx 25\,\text{seconds}$ |
| **E005** | `run_e005_experiment` | `config_path: Optional[Path]`, `seeds: List[int]`, `output_dir: Optional[Path]` | `artifacts/experiments/E005` | $\approx 45\,\text{seconds}$ |
| **E006** | `run_e006_experiment` | `config_path: Optional[Path]`, `seeds: List[int]`, `output_dir: Optional[Path]` | `artifacts/experiments/E006` | $\approx 20\,\text{seconds}$ |

### 3.2 CLI Runner Invocations
Each experiment can also be invoked via standard subprocess command:
```bash
python scripts/experiments/run_e001.py --seeds 42 123 456 789 1011 --output-dir artifacts/experiments/E001
python scripts/experiments/run_e002.py --seeds 42 123 456 789 1011 --output-dir artifacts/experiments/E002
python scripts/experiments/run_e003.py --seeds 42 123 456 789 1011 --output-dir artifacts/experiments/E003
python scripts/experiments/run_e004.py --seeds 42 123 456 789 1011 --output-dir artifacts/experiments/E004
python scripts/experiments/run_e005.py --seeds 42 123 456 789 1011 --output-dir artifacts/experiments/E005
python scripts/experiments/run_e006.py --seeds 42 123 456 789 1011 --output-dir artifacts/experiments/E006
```

---

## 4. Artifact Directory Layout & Canonical Inventory

The backend artifact streaming endpoint (`GET /api/v1/experiments/{id}/artifacts/{filename}`) serves files from `artifacts/experiments/{id}/`. 

### 4.1 Master Artifact Registry

```
artifacts/experiments/
├── E001/
│   ├── manifest.json              (Reproducibility metadata & hashes)
│   ├── report.md                  (Markdown research report)
│   ├── results.csv                (Per-severity metrics table)
│   ├── results.json               (Complete evaluation JSON)
│   ├── robustness_curve.png       (Publication-grade degradation curve)
│   └── failure_analysis.json      (Observed failure boundary details)
├── E002/
│   ├── manifest.json
│   ├── report.md
│   ├── aggregate_comparison.csv   (21 rows across 3 corruptions)
│   ├── aggregate_comparison.json  (Multi-seed statistical schema)
│   ├── robustness_comparison.png  (3-panel corruption comparison)
│   └── corruptions/{gaussian_noise, feature_missingness_mcar, feature_outliers}/
├── E003/
│   ├── manifest.json
│   ├── report.md
│   ├── aggregate_comparison.csv   (63 rows: 3 models × 3 corruptions × 7 severities)
│   ├── aggregate_comparison.json  (Complete cross-model JSON payload)
│   ├── robustness_comparison.png  (3-panel cross-model comparison)
│   └── models/{random_forest, logistic_regression, gradient_boosting}/
├── E004/
│   ├── manifest.json
│   ├── report.md
│   ├── sample_predictions.json    (9,450 atomic sample prediction records)
│   ├── sample_level_metrics.csv   (Sample error rates, margins, persistence)
│   ├── failure_patterns_summary.json (Class asymmetry, Jaccard similarities)
│   └── failure_patterns_analysis.png (4-panel microscopic failure visualization)
├── E005/
│   ├── reproducibility_manifest.json
│   ├── report.md
│   ├── feature_vulnerability_summary.csv (252 rows across 4 features)
│   ├── feature_rankings.json      (AUDC rankings, Friedman χ² stats, Wilcoxon FDR)
│   ├── metrics.json               (1,260-cell complete evaluation JSON)
│   └── figures/{feature_vulnerability_curves.png, feature_vulnerability_heatmap.png, ...}
└── E006/
    ├── reproducibility_manifest.json
    ├── report.md
    ├── shift_summary.csv          (525 cell evaluations across 5 shift regimes)
    ├── shift_comparisons.json     (Statistical hypothesis test outputs)
    ├── metrics.json               (Complete covariate shift evaluation JSON)
    └── figures/{covariate_shift_trajectories.png, directional_asymmetry.png, ...}
```

---

## 5. Progress Calculation & Lifecycle State Machine

### 5.1 Real Cell-Based Progress Calculation
In accordance with scientific reproducibility standards, **timer-based synthetic progress bars are prohibited**.

The backend worker must update `completed_cells` as evaluation cells conclude. Progress percentage is computed automatically by [`ExperimentProgressSchema`](file:///c:/Users/ishit/Model-Autopsy/ml_engine/src/model_autopsy/schemas/experiments.py):
$$\text{Progress} = \frac{\text{completed\_cells}}{\text{total\_cells}} \times 100.0\%$$
- **E001:** $1 \times 1 \times 7 \times 5 = 35\text{ cells}$
- **E002:** $1 \times 3 \times 7 \times 5 = 105\text{ cells}$
- **E003:** $3 \times 3 \times 7 \times 5 = 315\text{ cells}$
- **E004:** $3 \times 3 \times 7 \times 5 = 315\text{ cells}$ ($9{,}450$ sample evaluations)
- **E005:** $3 \times 3 \times 4 \times 7 \times 5 = 1{,}260\text{ cells}$
- **E006:** $3 \times 5 \times 7 \times 5 = 525\text{ cells}$

### 5.2 Lifecycle States & Cancellation Semantics
- Valid transitions: `DRAFT` $\to$ `QUEUED` $\to$ `RUNNING` $\to$ `COMPLETED` / `FAILED` / `CANCELLED`.
- **Cancellation Rule:** When `POST /api/v1/experiments/{id}/cancel` is invoked, Person 2's worker must issue `process.terminate()` (SIGTERM), poll for exit, and issue `process.kill()` (SIGKILL) if unstopped after a 5-second grace period. The API must return `confirmedStopped: true` only after verifying that the OS process has exited.

---

## 6. Security & Execution Constraints

1. **Path Traversal Defense in Artifact Streaming:**
   Person 2 must implement this exact path verification in `GET /api/v1/experiments/{id}/artifacts/{filename}`:
   ```python
   from pathlib import Path
   from fastapi import HTTPException

   BASE_ARTIFACT_DIR = Path("artifacts/experiments").resolve()
   ALLOWED_EXTENSIONS = {".json", ".csv", ".png", ".md", ".txt"}

   def get_secure_artifact_path(experiment_id: str, filename: str) -> Path:
       exp_dir = (BASE_ARTIFACT_DIR / experiment_id).resolve()
       target_path = (exp_dir / filename).resolve()
       
       # 1. Path traversal check
       if not target_path.is_relative_to(exp_dir):
           raise HTTPException(status_code=400, detail="Invalid path traversal sequence.")
           
       # 2. Extension check
       if target_path.suffix.lower() not in ALLOWED_EXTENSIONS:
           raise HTTPException(status_code=403, detail="File extension not permitted.")
           
       # 3. Existence check
       if not target_path.exists() or not target_path.is_file():
           raise HTTPException(status_code=404, detail="Artifact file not found.")
           
       return target_path
   ```
2. **Single-Job Concurrency Guard:**
   Keep experiment execution bounded to **1 active worker job**. If an execution request arrives while a job is `RUNNING`, either queue it in an in-memory queue or return HTTP `409 Conflict` with `ApiErrorResponse(code="ACTIVE_RUN_CONFLICT")`.
3. **Array Immutability:**
   All datasets ingested by `load_and_validate_iris()` enforce `flags.writeable = False`. Do not attempt in-place numpy array mutations.

---

## 7. Verification Commands for Person 2

Person 2 can execute these commands immediately to verify environment readiness:

1. **Verify Package Installation:**
   ```bash
   python -c "import model_autopsy; print('ML Engine import successful:', model_autopsy.__file__)"
   python -c "import backend.app.schemas as s; print('Backend schema re-export successful:', s.ExperimentRunRequest)"
   ```
2. **Verify Schema Test Suite:**
   ```bash
   pytest ml_engine/tests/test_schemas.py
   ```
3. **Verify All ML Protocol Tests:**
   ```bash
   pytest ml_engine/tests/test_e003_protocol.py ml_engine/tests/test_e004_protocol.py ml_engine/tests/test_schemas.py
   ```

---

## 8. Tests Person 2 Should Implement in `backend/tests/`

Person 2 is advised to implement these FastAPI integration tests:
- `test_health_endpoint`: Verify `GET /api/v1/health` returns status `200` and `healthy`.
- `test_list_experiments`: Verify `GET /api/v1/experiments` lists the 6 canonical experiments.
- `test_get_experiment_detail`: Verify `GET /api/v1/experiments/E003` loads and validates real `aggregate_comparison.json`.
- `test_artifact_streaming`: Verify `GET /api/v1/experiments/E003/artifacts/aggregate_comparison.csv` streams valid CSV headers.
- `test_path_traversal_rejection`: Verify `GET /api/v1/experiments/E003/artifacts/../../pyproject.toml` returns HTTP `400` or `403`.
- `test_concurrency_lock`: Verify submitting two concurrent runs triggers queuing or HTTP `409`.

---

## 9. Sign-Off & Handoff Clearance

Person 1's scientific and architectural deliverables are **100% complete, tested, and validated**:
- All 8 Research Questions (**RQ1–RQ8**) investigated and resolved.
- All 6 Experiments (**E001–E006**) implemented, executed, and scientifically audited.
- All 116 ML engine automated tests passing green.
- Canonical Pydantic v2 schemas fully tested and re-exported in `backend/app/schemas/`.
- Repository is clean and cleared for Person 2's FastAPI implementation.
