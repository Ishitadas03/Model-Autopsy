"""Tests for model adapter endpoints."""

import pytest
from httpx import AsyncClient


class TestModelEndpoints:
    """Test model adapter endpoints."""

    @pytest.mark.asyncio
    async def test_list_models(self, client: AsyncClient, seed_models):
        """Test GET /api/models returns list of models."""
        response = await client.get("/api/models")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4  # rf-iris, lr-iris, gb-iris, rf-german-credit

        # Check structure
        model = data[0]
        assert "id" in model
        assert "name" in model
        assert "description" in model
        assert "taskType" in model
        assert "supportedDatasets" in model
        assert "framework" in model
        assert "baselineF1" in model

    @pytest.mark.asyncio
    async def test_list_models_filtered_by_dataset(self, client: AsyncClient, seed_models):
        """Test GET /api/models?dataset_id=iris returns filtered models."""
        response = await client.get("/api/models?dataset_id=iris")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Should only return iris models
        for model in data:
            assert "iris" in model["supportedDatasets"]

    @pytest.mark.asyncio
    async def test_get_model(self, client: AsyncClient, seed_models):
        """Test GET /api/models/{model_id} returns specific model."""
        response = await client.get("/api/models/rf-iris")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "rf-iris"
        assert data["name"] == "Random Forest (Iris)"
        assert data["framework"] == "scikit-learn"
        assert data["baselineF1"] == 0.96

    @pytest.mark.asyncio
    async def test_get_nonexistent_model(self, client: AsyncClient, seed_models):
        """Test GET /api/models/{model_id} returns 404 for unknown model."""
        response = await client.get("/api/models/nonexistent")
        assert response.status_code == 404