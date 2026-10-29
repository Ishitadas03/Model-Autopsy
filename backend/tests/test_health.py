"""Tests for health endpoints."""

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test GET /api/health returns ok status."""
        response = await client.get("/api/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["mode"] == "live"
        assert "version" in data
        assert "database" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test GET / returns basic info."""
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Model Autopsy API"
        assert "version" in data
        assert data["status"] == "running"
        assert data["docs"] == "/docs"
        assert data["health"] == "/api/health"