"""Free-tier quota regression tests: reject unsafe jobs before persistence."""
import pytest

from app.core.config import settings


@pytest.mark.asyncio
async def test_embedded_rejects_too_many_seeds(monkeypatch, client):
    monkeypatch.setattr(settings, "JOB_EXECUTION_MODE", "embedded")
    response = await client.post("/api/experiments", json={
        "modelName": "RandomForest",
        "datasetName": "Iris",
        "datasetId": "iris",
        "taskType": "classification",
        "evaluationMetric": "f1",
        "failureThreshold": 0.7,
        "numSeeds": settings.EMBEDDED_MAX_SEEDS + 1,
    })
    assert response.status_code in (400, 422), response.text
    assert "seed" in response.text.lower()


@pytest.mark.asyncio
async def test_embedded_rejects_oversized_stress_grid(monkeypatch, client):
    monkeypatch.setattr(settings, "JOB_EXECUTION_MODE", "embedded")
    grid = [i / 100 for i in range(settings.EMBEDDED_MAX_SEVERITIES + 1)]
    response = await client.post("/api/experiments", json={
        "modelName": "RandomForest",
        "datasetId": "iris",
        "taskType": "classification",
        "evaluationMetric": "f1",
        "failureThreshold": 0.7,
        "severityLevels": grid,
    })
    assert response.status_code in (400, 422), response.text
    assert "stress" in response.text.lower() or "severity" in response.text.lower()


def test_embedded_resource_budget_is_bounded():
    assert settings.EMBEDDED_MAX_CSV_BYTES <= 3 * 1024 * 1024
    assert settings.EMBEDDED_MAX_CSV_ROWS <= 5000
    assert settings.EMBEDDED_MAX_SEEDS <= 2
    assert settings.EMBEDDED_MAX_ACTIVE_JOBS_PER_USER <= 2
