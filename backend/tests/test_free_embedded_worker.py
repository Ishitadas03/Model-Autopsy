"""Free-tier embedded queue: lifecycle and failure-safety tests."""
import asyncio

import pytest

from app.core.config import settings
from app.main import create_app, lifespan


@pytest.mark.asyncio
async def test_embedded_worker_starts_and_stops_with_web_lifespan(monkeypatch):
    import app.main as main_module
    from app.workers import experiment_worker

    started = asyncio.Event()
    stopped = asyncio.Event()

    async def ready_database():
        return None

    async def close_database():
        return None

    async def fake_worker(shutdown):
        started.set()
        await shutdown.wait()
        stopped.set()

    monkeypatch.setattr(settings, "JOB_EXECUTION_MODE", "embedded")
    monkeypatch.setattr(main_module, "init_db", ready_database)
    monkeypatch.setattr(main_module, "close_db", close_database)
    monkeypatch.setattr(experiment_worker, "serve_jobs", fake_worker)

    async with lifespan(create_app()):
        await asyncio.wait_for(started.wait(), timeout=2)
    assert stopped.is_set()


@pytest.mark.asyncio
async def test_embedded_worker_remains_off_if_database_is_not_ready(monkeypatch):
    import app.main as main_module
    from app.workers import experiment_worker

    spawned = []

    async def unavailable_database():
        raise RuntimeError("Schema migration required")

    async def close_database():
        return None

    async def fake_worker(shutdown):
        spawned.append(True)

    monkeypatch.setattr(settings, "JOB_EXECUTION_MODE", "embedded")
    monkeypatch.setattr(main_module, "init_db", unavailable_database)
    monkeypatch.setattr(main_module, "close_db", close_database)
    monkeypatch.setattr(experiment_worker, "serve_jobs", fake_worker)

    async with lifespan(create_app()):
        await asyncio.sleep(0)
    assert spawned == []


def test_embedded_budget_defaults_are_safe():
    assert settings.EMBEDDED_MAX_SEEDS >= 1
    assert settings.EMBEDDED_MAX_SEVERITIES >= 1
    assert settings.EMBEDDED_MAX_ACTIVE_JOBS_PER_USER >= 1
    assert settings.EMBEDDED_MAX_CSV_ROWS <= 5000
    assert settings.EMBEDDED_MAX_CSV_BYTES <= 3 * 1024 * 1024
