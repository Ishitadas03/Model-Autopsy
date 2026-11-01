"""Tests for dataset endpoints."""

import pytest
from httpx import AsyncClient


class TestDatasetEndpoints:
    """Test dataset endpoints."""

    @pytest.mark.asyncio
    async def test_list_datasets(self, client: AsyncClient, seed_datasets):
        """Test GET /api/datasets returns list of datasets."""
        response = await client.get("/api/datasets")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # iris and german-credit

        # Check structure
        dataset = data[0]
        assert "id" in dataset
        assert "name" in dataset
        assert "description" in dataset
        assert "taskType" in dataset
        assert "sampleCount" in dataset
        assert "featureCount" in dataset
        assert "license" in dataset
        assert "tags" in dataset

    @pytest.mark.asyncio
    async def test_get_dataset(self, client: AsyncClient, seed_datasets):
        """Test GET /api/datasets/{dataset_id} returns specific dataset."""
        response = await client.get("/api/datasets/iris")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "iris"
        assert data["name"] == "Iris Dataset"
        assert data["taskType"] == "classification"
        assert data["sampleCount"] == 150
        assert data["featureCount"] == 4

    @pytest.mark.asyncio
    async def test_get_nonexistent_dataset(self, client: AsyncClient, seed_datasets):
        """Test GET /api/datasets/{dataset_id} returns 404 for unknown dataset."""
        response = await client.get("/api/datasets/nonexistent")
        assert response.status_code == 404