"""Tests for failed samples pagination, filtering, and feature diffs."""

import pytest
from httpx import AsyncClient


class TestFailuresPagination:
    """Test failed samples retrieval."""

    @pytest.mark.asyncio
    async def test_failures_pagination_page_1(self, client: AsyncClient, seed_experiment):
        """Test GET /api/experiments/{id}/failures page 1."""
        response = await client.get("/api/experiments/EXP-0241/failures?page=1&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["samples"]) == 10

        sample = data["samples"][0]
        assert "id" in sample
        assert "sampleIndex" in sample
        assert "trueLabel" in sample
        assert "predictedLabel" in sample
        assert "confidence" in sample
        assert "noiseLevel" in sample
        assert "features" in sample
        assert "Income" in sample["features"]
        assert "clean" in sample["features"]["Income"]
        assert "stressed" in sample["features"]["Income"]

    @pytest.mark.asyncio
    async def test_failures_pagination_page_3(self, client: AsyncClient, seed_experiment):
        """Test GET /api/experiments/{id}/failures page 3 has remaining 5 samples."""
        response = await client.get("/api/experiments/EXP-0241/failures?page=3&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["samples"]) == 5

    @pytest.mark.asyncio
    async def test_failures_filtering_by_class(self, client: AsyncClient, seed_experiment):
        """Test filtering failed samples by ground truth/predicted class."""
        response = await client.get("/api/experiments/EXP-0241/failures?filterClass=Legitimate&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        for s in data["samples"]:
            assert s["trueLabel"] == "Legitimate" or s["predictedLabel"] == "Legitimate"

    @pytest.mark.asyncio
    async def test_failures_nonexistent_experiment(self, client: AsyncClient):
        """Test failure retrieval for nonexistent experiment returns 404."""
        response = await client.get("/api/experiments/EXP-9999/failures")
        assert response.status_code == 404

