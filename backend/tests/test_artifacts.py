"""Tests for artifact serving and canonical E003 artifacts."""

import pytest
from httpx import AsyncClient


class TestArtifactEndpoints:
    """Test artifact retrieval and multi-format serving."""

    @pytest.mark.asyncio
    async def test_get_e003_json(self, client: AsyncClient):
        """Test GET /api/experiments/e003 returns JSON comparison artifact."""
        response = await client.get("/api/experiments/e003")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "experiment_id" in data or "models" in data or "dataset_metadata" in data

    @pytest.mark.asyncio
    async def test_get_e003_csv(self, client: AsyncClient):
        """Test GET /api/experiments/e003?format=csv returns CSV."""
        response = await client.get("/api/experiments/e003?format=csv")
        assert response.status_code == 200
        text = response.text
        assert len(text) > 0
        assert "," in text

    @pytest.mark.asyncio
    async def test_get_e003_markdown(self, client: AsyncClient):
        """Test GET /api/experiments/e003?format=markdown returns markdown report."""
        response = await client.get("/api/experiments/e003?format=markdown")
        assert response.status_code == 200
        text = response.text
        assert len(text) > 0
        assert "#" in text

    @pytest.mark.asyncio
    async def test_get_e003_invalid_format(self, client: AsyncClient):
        """Test GET /api/experiments/e003 with unsupported format."""
        response = await client.get("/api/experiments/e003?format=xml")
        assert response.status_code == 404

