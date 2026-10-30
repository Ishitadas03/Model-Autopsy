"""Tests for experiments CRUD and API contract compliance."""

import pytest
from httpx import AsyncClient


class TestExperimentsCrud:
    """Test experiment CRUD endpoints against frontend contract."""

    @pytest.mark.asyncio
    async def test_list_experiments_empty(self, client: AsyncClient):
        """Test GET /api/experiments with no data."""
        response = await client.get("/api/experiments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_experiments_seeded(self, client: AsyncClient, seed_experiment):
        """Test GET /api/experiments returns contract-compliant experiment objects."""
        response = await client.get("/api/experiments")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        exp = next(e for e in data if e["id"] == "EXP-0241")
        assert exp["id"] == "EXP-0241"
        assert exp["modelName"] == "RandomForest-v2 (Credit)"
        assert exp["datasetName"] == "German Credit Benchmark"
        assert exp["datasetId"] == "german-credit"
        assert exp["taskType"] == "classification"
        assert exp["perturbationFamily"] == "gaussian_noise"
        assert exp["noiseType"] == "Gaussian Noise"
        assert exp["evaluationMetric"] == "f1"
        assert exp["failureThreshold"] == 0.80
        assert exp["seed"] == 42
        assert exp["status"] == "completed"
        assert exp["progressPercent"] == 100
        assert "createdAt" in exp

        # Results block verification
        results = exp["results"]
        assert results is not None
        assert results["baselineScore"] == 0.958
        assert results["worstCaseScore"] == 0.712
        assert results["observedBoundary"] == 0.231
        assert results["failedSamplesCount"] == 25
        assert isinstance(results["curveData"], list)
        assert len(results["curveData"]) == 7
        assert isinstance(results["featureVulnerabilities"], list)
        assert len(results["featureVulnerabilities"]) == 4

    @pytest.mark.asyncio
    async def test_get_experiment_by_id(self, client: AsyncClient, seed_experiment):
        """Test GET /api/experiments/{id} for single experiment."""
        response = await client.get("/api/experiments/EXP-0241")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "EXP-0241"
        assert data["modelName"] == "RandomForest-v2 (Credit)"
        assert "runs" in data
        assert len(data["runs"]) == 2
        assert data["runs"][0]["seed"] == 42

    @pytest.mark.asyncio
    async def test_get_nonexistent_experiment(self, client: AsyncClient):
        """Test GET /api/experiments/{id} with invalid ID returns 404."""
        response = await client.get("/api/experiments/EXP-9999")
        assert response.status_code == 404
        assert "EXP-9999" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_create_experiment_contract_payload(self, client: AsyncClient, seed_datasets, seed_models):
        """Test POST /api/experiments with frontend contract payload."""
        payload = {
            "modelName": "RandomForest-v2 (Credit)",
            "datasetName": "German Credit Benchmark",
            "datasetId": "german-credit",
            "taskType": "classification",
            "perturbationFamily": "gaussian_noise",
            "noiseType": "Gaussian Noise",
            "evaluationMetric": "f1",
            "failureThreshold": 0.80,
            "seed": 42,
        }
        response = await client.post("/api/experiments", json=payload)
        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["id"].startswith("EXP-")
        assert data["status"] in ("queued", "running", "completed")
        assert "createdAt" in data
        assert data["datasetId"] == "german-credit"

    @pytest.mark.asyncio
    async def test_create_experiment_invalid_polarity(self, client: AsyncClient):
        """Test POST /api/experiments rejects metric polarity violations."""
        # e.g., using regression metric MAE for classification task
        payload = {
            "modelName": "RandomForest-v2 (Credit)",
            "datasetName": "German Credit Benchmark",
            "datasetId": "german-credit",
            "taskType": "classification",
            "perturbationFamily": "gaussian_noise",
            "noiseType": "Gaussian Noise",
            "evaluationMetric": "mae",
            "failureThreshold": 0.80,
            "seed": 42,
        }
        response = await client.post("/api/experiments", json=payload)
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_cancel_experiment(self, client: AsyncClient, seed_experiment):
        """Test POST /api/experiments/{id}/cancel."""
        response = await client.post("/api/experiments/EXP-0241/cancel")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_experiment_progress(self, client: AsyncClient, seed_experiment):
        """Test GET /api/experiments/{id}/progress."""
        response = await client.get("/api/experiments/EXP-0241/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["experimentId"] == "EXP-0241"
        assert "progressPercent" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_list_experiments_filter_status(self, client: AsyncClient, seed_experiment):
        """Test GET /api/experiments?status=completed filtering."""
        response = await client.get("/api/experiments?status=completed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        for e in data:
            assert e["status"] == "completed"

