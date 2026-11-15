"""Security regressions: unauthenticated calls and cross-tenant objects must fail."""
from types import SimpleNamespace
from uuid import uuid4
import pytest

from app.core.auth import can_read_dataset, can_read_experiment
from app.core.config import settings


def test_dataset_and_experiment_owner_restrictions(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    owner = uuid4()
    other = uuid4()
    private_dataset = SimpleNamespace(owner_id=owner, is_public=False)
    benchmark = SimpleNamespace(owner_id=None, is_public=True)
    unowned_legacy = SimpleNamespace(owner_id=None, is_public=False)
    private_experiment = SimpleNamespace(owner_id=owner)

    assert can_read_dataset(private_dataset, owner)
    assert not can_read_dataset(private_dataset, other)
    assert not can_read_dataset(unowned_legacy, owner)
    assert can_read_dataset(benchmark, owner)
    assert not can_read_experiment(private_experiment, other)
    assert can_read_experiment(private_experiment, owner)
    assert not can_read_experiment(SimpleNamespace(owner_id=None), owner)


@pytest.mark.asyncio
async def test_production_rejects_anonymous_private_api(monkeypatch, client):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "AUTH_REQUIRED", True)
    for method, uri in [
        ("get", "/api/experiments"),
        ("get", "/api/datasets"),
        ("post", "/api/experiments"),
        ("get", "/api/experiments/EXP-0001/artifacts/results.json"),
        ("get", "/api/storage/status"),
    ]:
        response = await getattr(client, method)(uri)
        assert response.status_code == 401, (uri, response.text)


@pytest.mark.asyncio
async def test_experiment_results_are_private_between_authenticated_users(client, seed_experiment, test_session):
    """HTTP endpoints must enforce ownership even with a valid identity."""
    from app.main import app
    from app.core.auth import get_current_user
    from app.models.experiment import Experiment
    owner, stranger = uuid4(), uuid4()
    exp = await test_session.get(Experiment, seed_experiment.id)
    exp.owner_id = owner
    await test_session.flush()

    try:
        app.dependency_overrides[get_current_user] = lambda: stranger
        for path in (
            "/api/experiments/EXP-0241",
            "/api/experiments/EXP-0241/progress",
            "/api/experiments/EXP-0241/artifacts/results.json",
        ):
            response = await client.get(path)
            assert response.status_code == 404, (path, response.text)
        listing = await client.get("/api/experiments")
        assert listing.status_code == 200
        assert not any(row["id"] == "EXP-0241" for row in listing.json())

        app.dependency_overrides[get_current_user] = lambda: owner
        own = await client.get("/api/experiments/EXP-0241")
        assert own.status_code == 200, own.text
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_health_endpoint_does_not_reveal_r2_bucket(client):
    """Public liveness response is intentionally non-sensitive."""
    response = await client.get("/api/health")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "bucket_name" not in body.get("storage", {})
    assert "access_details" not in body.get("storage", {})
