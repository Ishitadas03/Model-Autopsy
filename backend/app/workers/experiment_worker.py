"""Single-process durable experiment worker.

Runs embedded in the web process or in a separate worker. PostgreSQL SKIP LOCKED prevents
two worker instances from claiming the same queued experiment. Expired leases
are marked failed, not automatically replayed: ML jobs can have side effects
(e.g. persisted artifacts) and blindly retrying creates duplicate records.
"""
from __future__ import annotations

import asyncio
import os
import signal
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.database import session_context
from app.core.logging import get_logger, setup_logging
from app.models.experiment import Experiment, ExperimentStatus
from app.services.experiment_service import ExperimentService
from app.services.ml_engine_bridge import ml_engine_bridge

logger = get_logger(__name__)
WORKER_ID = f"{os.getenv('HOSTNAME', 'worker')}-{uuid.uuid4().hex[:12]}"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def claim_next_job() -> tuple[uuid.UUID, str, dict] | None:
    async with session_context() as session:
        record = (
            await session.execute(
                select(Experiment)
                .where(
                    Experiment.status == ExperimentStatus.QUEUED,
                    Experiment.execution_payload.is_not(None),
                )
                .order_by(Experiment.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
        ).scalar_one_or_none()
        if record is None:
            return None
        record.status = ExperimentStatus.RUNNING
        record.lease_owner = WORKER_ID
        record.lease_expires_at = now_utc() + timedelta(seconds=settings.WORKER_LEASE_SECONDS)
        record.attempt_count += 1
        record.started_at = now_utc()
        return record.id, record.experiment_id, dict(record.execution_payload)


async def mark_abandoned() -> int:
    """No automatic retries after a crash: fail expired jobs and expose reason."""
    count = 0
    async with session_context() as session:
        rows = (
            await session.execute(
                select(Experiment)
                .where(
                    Experiment.status == ExperimentStatus.RUNNING,
                    Experiment.lease_expires_at.is_not(None),
                    Experiment.lease_expires_at < now_utc(),
                )
                .with_for_update(skip_locked=True)
            )
        ).scalars().all()
        for exp in rows:
            await ExperimentService(session)._mark_experiment_failed(
                session, exp.id,
                "Worker lease expired. Verify artifacts before manually re-submitting.",
                expected_lease_owner=exp.lease_owner,
            )
            exp.lease_owner = None
            exp.lease_expires_at = None
            count += 1
    if count:
        logger.warning("Marked abandoned ML jobs as failed", count=count)
    return count


async def heartbeat(experiment_db_id: uuid.UUID, experiment_id: str, task: asyncio.Task) -> None:
    while not task.done():
        await asyncio.sleep(max(3, settings.WORKER_LEASE_SECONDS // 3))
        if task.done():
            return
        try:
            async with session_context() as session:
                exp = await session.get(Experiment, experiment_db_id, with_for_update=True)
                if not exp or not ExperimentService._owns_live_lease(exp, WORKER_ID):
                    logger.warning("Experiment lease lost or cancelled", experiment_id=experiment_id)
                    task.cancel()
                    return
                exp.lease_expires_at = now_utc() + timedelta(seconds=settings.WORKER_LEASE_SECONDS)
        except Exception:
            logger.exception("ML job heartbeat failed", experiment_id=experiment_id)
            # A failed heartbeat will eventually expire the lease. Never
            # report success without checking ownership before final commit.


async def run_claimed_job(job: tuple[uuid.UUID, str, dict]) -> None:
    experiment_db_id, experiment_id, payload = job
    experiment_type = ExperimentService._get_experiment_type(None, payload.get("perturbation_family", "gaussian_noise"))
    async with session_context() as session:
        service = ExperimentService(session)
    run = asyncio.create_task(service._run_experiment_background(
        experiment_db_id, experiment_type, payload, expected_lease_owner=WORKER_ID,
    ))
    hb = asyncio.create_task(heartbeat(experiment_db_id, experiment_id, run))
    failure_reason = None
    try:
        await asyncio.wait_for(run, timeout=settings.EXPERIMENT_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        logger.error("ML experiment reached execution timeout", experiment_id=experiment_id)
        failure_reason = "Experiment timed out"
    except asyncio.CancelledError:
        # Child cancellation (user cancel / lost lease) must not stop the queue.
        # Cancellation of THIS task is process shutdown and must propagate.
        if asyncio.current_task().cancelling():
            failure_reason = "Worker stopped before experiment completed"
            raise
        failure_reason = "Experiment execution stopped before completion"
    except Exception:
        failure_reason = "Worker could not complete experiment execution"
        logger.exception("Claimed experiment execution failed", experiment_id=experiment_id)
    finally:
        hb.cancel()
        await asyncio.gather(hb, return_exceptions=True)
        if not run.done():
            run.cancel()
        await asyncio.gather(run, return_exceptions=True)
        await ml_engine_bridge.cancel_experiment(experiment_id)
        async with session_context() as session:
            exp = await session.get(Experiment, experiment_db_id, with_for_update=True)
            if exp and exp.lease_owner == WORKER_ID:
                if exp.status == ExperimentStatus.RUNNING:
                    await ExperimentService(session)._mark_experiment_failed(
                        session, experiment_db_id,
                        failure_reason or "Experiment returned without a committed result",
                        expected_lease_owner=WORKER_ID,
                    )
                # Release only after a terminal state is committed in the same
                # transaction. On DB failure the lease remains recoverable.
                exp.lease_owner = None
                exp.lease_expires_at = None



async def serve_jobs(shutdown: asyncio.Event) -> None:
    """Run the durable queue in a worker service or an embedded free web instance."""
    if settings.WORKER_LEASE_SECONDS < 30:
        raise RuntimeError("Worker lease must be at least 30 seconds")
    logger.info(
        "Started database-backed experiment job polling",
        worker_id=WORKER_ID,
        execution_mode=settings.JOB_EXECUTION_MODE,
    )
    while not shutdown.is_set():
        try:
            await mark_abandoned()
            job = await claim_next_job()
            if job:
                await run_claimed_job(job)
                continue
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Worker poll/claim failed; will retry")
        try:
            await asyncio.wait_for(
                shutdown.wait(),
                timeout=max(1, settings.WORKER_POLL_SECONDS),
            )
        except asyncio.TimeoutError:
            pass

async def main() -> None:
    setup_logging()
    if settings.JOB_EXECUTION_MODE != "worker":
        raise RuntimeError("Worker service must use JOB_EXECUTION_MODE=worker")
    if settings.WORKER_LEASE_SECONDS < 30:
        raise RuntimeError("Worker lease must be at least 30 seconds")
    shutdown = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, shutdown.set)
        except NotImplementedError:
            pass

    await serve_jobs(shutdown)


if __name__ == "__main__":
    asyncio.run(main())
