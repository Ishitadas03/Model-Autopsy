"""Queue cancellation, shutdown and lease fencing against a real test database."""
import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.config import settings
from app.models.experiment import Experiment, ExperimentRun, ExperimentStatus as Status
from app.services import experiment_service as service_module
from app.services.experiment_service import ExperimentService
from app.workers import experiment_worker as worker


@pytest_asyncio.fixture
async def claimed_job(monkeypatch, test_engine, test_session, seed_experiment):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    @asynccontextmanager
    async def sessions():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                await session.rollback()
                raise

    monkeypatch.setattr(worker, "session_context", sessions)
    monkeypatch.setattr(service_module, "session_context", sessions)
    monkeypatch.setattr(worker.ml_engine_bridge, "cancel_experiment", AsyncMock())
    exp = seed_experiment
    exp.status = Status.RUNNING
    exp.lease_owner = worker.WORKER_ID
    exp.lease_expires_at = worker.now_utc() + timedelta(seconds=90)
    exp.completed_at = None
    runs = (await test_session.execute(select(ExperimentRun))).scalars().all()
    for run in runs:
        run.status = Status.RUNNING
        run.completed_at = None
    await test_session.commit()
    return (exp.id, exp.experiment_id, {"experiment_id": exp.experiment_id}), sessions


async def read_state(job, sessions):
    async with sessions() as session:
        exp = await session.get(Experiment, job[0])
        runs = (await session.execute(select(ExperimentRun).where(
            ExperimentRun.experiment_id == job[0],
        ))).scalars().all()
        return exp, runs


@pytest.mark.asyncio
async def test_timeout_is_failed_and_clears_runs_and_lease(monkeypatch, claimed_job):
    job, sessions = claimed_job
    monkeypatch.setattr(settings, "EXPERIMENT_TIMEOUT_SECONDS", 0.05)

    async def stalled(**kwargs):
        await asyncio.Event().wait()

    monkeypatch.setattr(worker.ml_engine_bridge, "run_experiment", stalled)
    await worker.run_claimed_job(job)
    exp, runs = await read_state(job, sessions)
    assert exp.status == Status.FAILED
    assert exp.error_message == "Experiment timed out"
    assert exp.lease_owner is None and exp.lease_expires_at is None
    assert all(r.status == Status.FAILED and r.completed_at for r in runs)


@pytest.mark.asyncio
async def test_shutdown_propagates_and_leaves_recoverable_terminal_state(monkeypatch, claimed_job):
    job, sessions = claimed_job
    started = asyncio.Event()
    stopped = asyncio.Event()

    async def stalled(**kwargs):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    monkeypatch.setattr(worker.ml_engine_bridge, "run_experiment", stalled)
    task = asyncio.create_task(worker.run_claimed_job(job))
    await asyncio.wait_for(started.wait(), timeout=2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert stopped.is_set()
    exp, runs = await read_state(job, sessions)
    assert exp.status == Status.FAILED
    assert "Worker stopped" in exp.error_message
    assert exp.lease_owner is None
    assert all(r.status == Status.FAILED for r in runs)


@pytest.mark.asyncio
async def test_child_cancel_does_not_stop_queue(monkeypatch, claimed_job):
    job, sessions = claimed_job
    shutdown = asyncio.Event()
    claims = []

    async def child_cancel(self, *args, **kwargs):
        raise asyncio.CancelledError()

    async def claim():
        claims.append(True)
        if len(claims) == 1:
            return job
        shutdown.set()
        return None

    monkeypatch.setattr(ExperimentService, "_run_experiment_background", child_cancel)
    monkeypatch.setattr(worker, "claim_next_job", claim)
    await asyncio.wait_for(worker.serve_jobs(shutdown), timeout=2)
    assert len(claims) == 2
    exp, _ = await read_state(job, sessions)
    assert exp.status == Status.FAILED


@pytest.mark.asyncio
async def test_expired_lease_fails_runs_too(claimed_job):
    job, sessions = claimed_job
    async with sessions() as session:
        exp = await session.get(Experiment, job[0])
        exp.lease_expires_at = worker.now_utc() - timedelta(seconds=1)
    assert await worker.mark_abandoned() == 1
    exp, runs = await read_state(job, sessions)
    assert exp.status == Status.FAILED and exp.lease_owner is None
    assert all(r.status == Status.FAILED for r in runs)


@pytest.mark.asyncio
async def test_stale_worker_cannot_fail_another_workers_job(claimed_job):
    job, sessions = claimed_job
    async with sessions() as session:
        await ExperimentService(session)._mark_experiment_failed(
            session, job[0], "stale error", expected_lease_owner="old-worker",
        )
    exp, runs = await read_state(job, sessions)
    assert exp.status == Status.RUNNING
    assert all(r.status == Status.RUNNING for r in runs)


@pytest.mark.asyncio
async def test_cancel_is_committed_before_subprocess_termination(monkeypatch, claimed_job):
    job, sessions = claimed_job

    async def terminate(experiment_id):
        exp, runs = await read_state(job, sessions)
        assert exp.status == Status.CANCELLED
        assert all(r.status == Status.CANCELLED for r in runs)
        return {"confirmed_stopped": True}

    monkeypatch.setattr(worker.ml_engine_bridge, "cancel_experiment", terminate)
    async with sessions() as session:
        result = await ExperimentService(session).cancel_experiment(job[0])
    assert result["status"] == "cancelled"


@pytest.mark.asyncio
async def test_failed_old_worker_does_not_modify_completed_runs(claimed_job):
    job, sessions = claimed_job
    async with sessions() as session:
        exp = await session.get(Experiment, job[0])
        exp.status = Status.COMPLETED
        await session.flush()
        await ExperimentService(session)._mark_experiment_failed(session, job[0], "late error")
    exp, runs = await read_state(job, sessions)
    assert exp.status == Status.COMPLETED
    assert all(r.status == Status.RUNNING for r in runs)


@pytest.mark.asyncio
async def test_expired_lease_cannot_commit_success(monkeypatch, claimed_job):
    job, sessions = claimed_job

    async def finish_after_expiry(**kwargs):
        async with sessions() as session:
            exp = await session.get(Experiment, job[0])
            exp.lease_expires_at = worker.now_utc() - timedelta(seconds=1)
        return {}

    save_results = AsyncMock()
    monkeypatch.setattr(worker.ml_engine_bridge, "run_experiment", finish_after_expiry)
    monkeypatch.setattr(ExperimentService, "_process_and_save_results", save_results)
    await worker.run_claimed_job(job)
    save_results.assert_not_awaited()
    exp, runs = await read_state(job, sessions)
    assert exp.status == Status.FAILED
    assert all(r.status == Status.FAILED for r in runs)
