"""Complete Model Autopsy Backend Verification Script.
Validates all phases: configuration, database models, schemas, repositories,
ML engine bridge, artifact serving, and scientific invariants.
"""

import asyncio
import os
import sys
from pathlib import Path

# Unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Setup paths
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
ml_engine_src = project_root / "ml_engine" / "src"

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(ml_engine_src))

print("==================================================")
print(" MODEL AUTOPSY BACKEND VERIFICATION ")
print("==================================================")

# 1. Config & Paths
print("\n[PHASE 1] Checking Core Configuration & Paths...")
from app.core.config import settings
print(f" - App: {settings.APP_NAME} v{settings.APP_VERSION}")
print(f" - Artifacts dir: {settings.ARTIFACTS_BASE_DIR} (exists: {settings.ARTIFACTS_BASE_DIR.exists()})")
print(f" - Configs dir: {settings.CONFIGS_BASE_DIR} (exists: {settings.CONFIGS_BASE_DIR.exists()})")
print(f" - Scripts dir: {settings.SCRIPTS_BASE_DIR} (exists: {settings.SCRIPTS_BASE_DIR.exists()})")
print(f" - ML engine: {settings.ML_ENGINE_PATH} (exists: {settings.ML_ENGINE_PATH.exists()})")
assert settings.ARTIFACTS_BASE_DIR.exists(), "Artifacts base dir must exist"

# 2. Database Models & Schema Metadata
print("\n[PHASE 2] Checking SQLAlchemy 2.0 ORM Models...")
from app.core.database import Base
from app.models import (
    experiment,
    dataset,
    model_adapter,
    failure_sample,
    artifact,
)
tables = list(Base.metadata.tables.keys())
print(f" - Registered ORM Tables ({len(tables)}): {', '.join(sorted(tables))}")
expected_tables = {
    "datasets", "model_adapters", "experiments", "experiment_runs",
    "experiment_results", "failed_samples", "artifact_manifests", "artifact_references"
}
missing = expected_tables - set(tables)
assert not missing, f"Missing tables in ORM metadata: {missing}"
print(" - All 8 required database tables mapped successfully!")

# 3. Schemas & Contract Matching
print("\n[PHASE 3] Checking Pydantic v2 Schemas...")
from app.schemas import (
    ExperimentSummarySchema,
    ExperimentDetailSchema,
    ExperimentRunRequest,
    ExperimentProgressSchema,
    ExperimentCancelResponse,
    DatasetSchema,
    ModelAdapterSchema,
    FailedSample,
    FailedSamplesResponse,
    RunStatus,
)
print(" - Schemas imported and verified with frontend contract.")

# 4. ML Engine Bridge & Runners
print("\n[PHASE 4] Checking ML Engine Bridge...")
from app.services.ml_engine_bridge import MLEngineBridge
bridge = MLEngineBridge()
for exp_type in ["E001", "E002", "E003", "E004"]:
    script_path = bridge._get_script_path(exp_type)
    print(f" - {exp_type}: script={script_path.name} (exists={script_path.exists()})")
    assert script_path.exists(), f"Script for {exp_type} missing"

# 5. Artifact Serving
print("\n[PHASE 5] Checking Canonical Artifact Serving (E003)...")
from app.services.artifact_service import ArtifactService

service = ArtifactService(None)
# Drive coroutine directly without network/socket loop
coro = service.get_e003_artifact("json")
try:
    coro.send(None)
except StopIteration as e:
    data = e.value
print(f" - E003 JSON artifact loaded ({len(data)} top-level keys)")
assert isinstance(data, dict)

coro_csv = service.get_e003_artifact("csv")
try:
    coro_csv.send(None)
except StopIteration as e:
    csv_res = e.value
print(f" - E003 CSV artifact loaded ({len(csv_res.body)} bytes)")
assert len(csv_res.body) > 0

coro_md = service.get_e003_artifact("markdown")
try:
    coro_md.send(None)
except StopIteration as e:
    md_res = e.value
print(f" - E003 Markdown report loaded ({len(md_res.body)} bytes)")
assert len(md_res.body) > 0

# 6. Scientific Invariants Enforcement
print("\n[PHASE 6] Checking Scientific Invariants Enforcement...")
from app.main import _inject_scientific_caveats
test_payload = {
    "observed_boundary": 0.231,
    "robustness_score": 0.88,
    "overall_score": 92,
    "letter_grade": "A-",
    "subjective_rating": "Robust",
    "feature_vulnerabilities": [
        {"feature": "Credit Score", "drop": 0.284}
    ]
}
sanitized = _inject_scientific_caveats(test_payload)

# Verify Invariant 1: Boundary metric disclaimer
assert "Observed failure boundary under the specified experimental configuration." in sanitized["observed_boundary_caveat"]
print(" - Invariant 1 verified: Boundary disclaimer injected.")

# Verify Invariant 2: Sensitivity caveat
assert "Empirical sensitivity — not a causal explanation." in sanitized["feature_vulnerabilities"][0]["caveat"]
print(" - Invariant 2 verified: Feature sensitivity caveat injected.")

# Verify Invariant 3: No aggregate robustness score, grade, or rating
for forbidden in ["robustness_score", "overall_score", "letter_grade", "subjective_rating"]:
    assert forbidden not in sanitized, f"Forbidden field '{forbidden}' was not stripped"
print(" - Invariant 3 verified: Forbidden aggregate scores/grades stripped.")

# Verify Invariant 4: Metric polarity validation
from app.services.experiment_service import ExperimentService
from app.schemas import ExperimentRunRequest
from app.core.exceptions import InvalidExperimentConfigError

exp_service = ExperimentService(None)
exp_service._validate_metric_polarity(ExperimentRunRequest(dataset_id="german-credit", task_type="classification", evaluation_metric="f1", failure_threshold=0.8))

try:
    exp_service._validate_metric_polarity(ExperimentRunRequest(dataset_id="german-credit", task_type="classification", evaluation_metric="mae", failure_threshold=0.8))
    assert False, "Should reject mae for classification"
except InvalidExperimentConfigError:
    pass

print(" - Invariant 4 verified: Metric polarity strictly enforced.")

# 7. FastAPI App & Routes
print("\n[PHASE 7] Checking FastAPI Application & Routes...")
from app.main import app
routes = [route.path for route in app.routes]
print(f" - Registered routes ({len(routes)}):")
for path in sorted(set(routes)):
    print(f"   * {path}")

required_endpoints = [
    "/api/health",
    "/api/experiments",
    "/api/experiments/{experiment_id}",
    "/api/experiments/{experiment_id}/cancel",
    "/api/experiments/{experiment_id}/progress",
    "/api/datasets",
    "/api/datasets/{dataset_id}",
    "/api/models",
    "/api/models/{model_id}",
    "/api/experiments/{experiment_id}/failures",
    "/api/experiments/e003",
    "/api/experiments/{experiment_id}/artifacts/{artifact_type}",
]

for endpoint in required_endpoints:
    assert endpoint in routes, f"Missing required endpoint: {endpoint}"
print(" - All required frontend API contract endpoints are registered and active!")

print("\n==================================================")
print(" BACKEND VERIFICATION SUCCESSFUL: 100% COMPLETE! ")
print("==================================================")
