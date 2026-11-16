"""HTTP upload -> baseline -> queue -> subprocess -> private artifact download.

Uses isolated local storage. Live Supabase/R2 verification is a separate gate.
"""
import hashlib
import shutil
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_session
from app.main import app
from app.services import experiment_service as service_module
from app.services.dataset_loader import load_registered_csv
from app.services.storage_service import storage_service
from app.workers import experiment_worker as worker


@pytest.mark.asyncio
@pytest.mark.parametrize("task,metric", [("classification", "f1"), ("regression", "r2")])
async def test_uploaded_csv_completes_full_workflow(task, metric, client, test_engine, test_session, tmp_path, monkeypatch):
    dataset_dir = tmp_path / "datasets"
    artifact_dir = tmp_path / "artifacts"
    for key, path in (("DATASETS_BASE_DIR", dataset_dir), ("ARTIFACTS_BASE_DIR", artifact_dir)):
        monkeypatch.setattr(settings, key, path)
        monkeypatch.setenv(key, str(path))
    monkeypatch.setattr(settings, "JOB_EXECUTION_MODE", "embedded")
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "local")
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setattr(storage_service, "access_key_id", None)
    monkeypatch.setattr(worker.ml_engine_bridge, "artifacts_dir", artifact_dir)
    owner, stranger = uuid4(), uuid4()
    app.dependency_overrides[get_current_user] = lambda: owner
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    @asynccontextmanager
    async def sessions():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                await session.rollback()
                raise

    monkeypatch.setattr(worker, "session_context", sessions)
    monkeypatch.setattr(service_module, "session_context", sessions)
    async def request_session():
        async with sessions() as session:
            yield session
    app.dependency_overrides[get_session] = request_session
    rows = ["feature_a,feature_b,target"]
    for i in range(80):
        target = str(i % 2) if task == "classification" else str(2.5 * i + (i % 3))
        rows.append(f"{i},{i % 7},{target}")
    csv = ("\n".join(rows) + "\n").encode()
    response = await client.post("/api/datasets/upload", files={"file": ("dataset.csv", csv, "text/csv")}, data={
        "dataset_id": "CustomCase", "target_name": "target", "task_type": task,
    })
    assert response.status_code == 201, response.text
    dataset_id = response.json()["id"]
    assert "CustomCase" in dataset_id
    model = "random-forest-classifier" if task == "classification" else "random-forest-regressor"
    payload = {"datasetId": dataset_id, "modelId": model, "taskType": task,
               "targetName": "target", "modelParams": {"n_estimators": 10}, "seed": 42}
    baseline = await client.post("/api/experiments/baseline", json=payload)
    assert baseline.status_code == 200, baseline.text
    assert baseline.json()["sampleCount"] == 80
    assert metric in baseline.json()["metrics"]
    queued = await client.post("/api/experiments", json={
        **payload, "modelName": model, "datasetName": "Custom upload",
        "evaluationMetric": metric, "failureThreshold": 0.8,
        "perturbationFamily": "gaussian_noise", "severityLevels": [0, 0.2], "seeds": [42],
    })
    assert queued.status_code == 201, queued.text
    experiment_id = queued.json()["id"]
    job = await worker.claim_next_job()
    assert job is not None and job[1] == experiment_id
    assert job[2]["dataset_sha256"] == hashlib.sha256(csv).hexdigest()
    await worker.run_claimed_job(job)
    test_session.expire_all()
    result = await client.get(f"/api/experiments/{experiment_id}")
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "completed", result.text
    assert len(result.json()["results"]["curveData"]) == 2
    assert all(r["status"] == "completed" for r in result.json()["runs"])

    saved = {}
    for name in ("results.json", "curves.csv", "report.md", "manifest.json"):
        artifact = await client.get(f"/api/experiments/{experiment_id}/artifacts/{name}")
        assert artifact.status_code == 200, artifact.text
        assert hashlib.sha256(artifact.content).hexdigest() == artifact.headers["x-sha256"]
        saved[f"experiments/{experiment_id}/{name}"] = artifact.content

    # Simulate fresh instance plus remote persisted bytes. This is not a live R2 test.
    shutil.rmtree(artifact_dir)
    monkeypatch.setattr(settings, "STORAGE_PROVIDER", "r2")
    monkeypatch.setattr(storage_service, "get_object_bytes_from_r2", lambda key: saved.get(key))
    remote = await client.get(f"/api/experiments/{experiment_id}/artifacts/results.json")
    assert remote.status_code == 200, remote.text
    assert remote.content == saved[f"experiments/{experiment_id}/results.json"]
    saved[f"experiments/{experiment_id}/results.json"] = b"changed remotely"
    assert (await client.get(f"/api/experiments/{experiment_id}/artifacts/results.json")).status_code == 503
    saved.clear()
    assert (await client.get(f"/api/experiments/{experiment_id}/artifacts/results.json")).status_code == 503

    app.dependency_overrides[get_current_user] = lambda: stranger
    for path in (f"/api/datasets/{dataset_id}", f"/api/experiments/{experiment_id}",
                 f"/api/experiments/{experiment_id}/artifacts/results.json"):
        assert (await client.get(path)).status_code == 404
    assert (await client.post("/api/experiments/baseline", json=payload)).status_code == 404


def test_registered_dataset_checksum_mismatch_is_rejected(monkeypatch):
    monkeypatch.setattr(storage_service, "retrieve_bytes", lambda key: b"feature,target\n1,2\n")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_registered_csv("sample", expected_sha256="0" * 64)
