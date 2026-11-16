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
        # Dataset-specific adapters may be returned alongside generic adapters
        # that support all uploaded or benchmark datasets.
        for model in data:
            supported = model["supportedDatasets"]
            assert supported == [] or "iris" in supported

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

    @pytest.mark.asyncio
    async def test_generic_models_support_classification_and_regression(self, client: AsyncClient):
        """The live API catalog must support custom regression CSVs without UI mocks."""
        response = await client.get("/api/models")
        assert response.status_code == 200, response.text
        rows = response.json()
        generic = [row for row in rows if row["id"].startswith("generic-")]
        assert any(row["taskType"] == "classification" for row in generic)
        assert any(row["taskType"] == "regression" for row in generic)
        assert all(row["framework"] == "scikit-learn" for row in generic)
        assert all(row["supportedDatasets"] == [] for row in generic)

    @pytest.mark.asyncio
    async def test_generic_model_lookup(self, client: AsyncClient):
        response = await client.get("/api/models/generic-rf-regressor")
        assert response.status_code == 200, response.text
        row = response.json()
        assert row["taskType"] == "regression"
        assert row["predictProba"] is False
        assert row["parameters"]["n_estimators"] == 100

    @pytest.mark.asyncio
    async def test_private_model_adapters_are_not_disclosed_to_other_users(
        self, client: AsyncClient, seed_models, test_session
    ):
        """A registered adapter inherits the source dataset's tenant visibility."""
        from uuid import uuid4
        from sqlalchemy import select
        from app.core.auth import get_current_user
        from app.main import app
        from app.models.dataset import Dataset

        private_owner, another_user = uuid4(), uuid4()
        dataset = (await test_session.execute(
            select(Dataset).where(Dataset.dataset_id == "iris")
        )).scalar_one()
        dataset.owner_id = private_owner
        dataset.is_public = False
        await test_session.flush()

        try:
            app.dependency_overrides[get_current_user] = lambda: another_user
            foreign_list = await client.get("/api/models?dataset_id=iris")
            assert foreign_list.status_code == 200, foreign_list.text
            assert all(
                model["id"] not in {"rf-iris", "lr-iris", "gb-iris"}
                for model in foreign_list.json()
            )
            detail = await client.get("/api/models/rf-iris")
            assert detail.status_code == 404

            app.dependency_overrides[get_current_user] = lambda: private_owner
            own_list = await client.get("/api/models?dataset_id=iris")
            assert own_list.status_code == 200
            assert any(model["id"] == "rf-iris" for model in own_list.json())
            own_detail = await client.get("/api/models/rf-iris")
            assert own_detail.status_code == 200
        finally:
            app.dependency_overrides.pop(get_current_user, None)
