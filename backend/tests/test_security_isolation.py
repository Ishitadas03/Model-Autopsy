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
    ]:
        response = await getattr(client, method)(uri)
        assert response.status_code == 401, (uri, response.text)
