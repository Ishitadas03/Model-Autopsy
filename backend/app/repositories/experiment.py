"""Experiment repository for data access."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.experiment import Experiment, ExperimentRun, ExperimentResult, ExperimentStatus
from app.repositories.base import BaseRepository


class ExperimentRepository(BaseRepository[Experiment]):
    """Repository for experiment operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Experiment)

    async def get_by_experiment_id(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by human-readable experiment_id (e.g., EXP-0241) with relationships."""
        result = await self.session.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.runs),
                selectinload(Experiment.result),
                selectinload(Experiment.failed_samples),
                selectinload(Experiment.artifacts),
            )
            .where(Experiment.experiment_id == experiment_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, order_by: str = "created_at"
    ) -> List[Experiment]:
        """Get all experiments with result and runs loaded."""
        order_column = getattr(Experiment, order_by, Experiment.created_at)
        result = await self.session.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.runs),
                selectinload(Experiment.result),
            )
            .order_by(order_column.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_details(self, id_: UUID) -> Optional[Experiment]:
        """Get experiment with all relationships loaded."""
        result = await self.session.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.runs),
                selectinload(Experiment.result),
                selectinload(Experiment.failed_samples),
                selectinload(Experiment.artifacts),
            )
            .where(Experiment.id == id_)
        )
        return result.scalar_one_or_none()

    async def get_by_status(
        self, status: ExperimentStatus, skip: int = 0, limit: int = 100
    ) -> List[Experiment]:
        """Get experiments by status with result and runs loaded."""
        result = await self.session.execute(
            select(Experiment)
            .options(
                selectinload(Experiment.runs),
                selectinload(Experiment.result),
            )
            .where(Experiment.status == status)
            .order_by(Experiment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_running_experiments(self) -> List[Experiment]:
        """Get all currently running experiments."""
        result = await self.session.execute(
            select(Experiment).where(
                Experiment.status.in_([ExperimentStatus.QUEUED, ExperimentStatus.RUNNING])
            )
        )
        return list(result.scalars().all())

    async def get_next_experiment_id(self) -> str:
        """Generate next experiment ID (EXP-XXXX)."""
        result = await self.session.execute(
            select(func.max(Experiment.experiment_id))
        )
        max_id = result.scalar_one_or_none()
        if max_id and max_id.startswith("EXP-"):
            try:
                num = int(max_id.split("-")[1])
                return f"EXP-{num + 1:04d}"
            except (ValueError, IndexError):
                pass
        return "EXP-0001"


class ExperimentRunRepository(BaseRepository[ExperimentRun]):
    """Repository for experiment run operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ExperimentRun)

    async def get_by_experiment(self, experiment_id: UUID) -> List[ExperimentRun]:
        """Get all runs for an experiment."""
        result = await self.session.execute(
            select(ExperimentRun)
            .where(ExperimentRun.experiment_id == experiment_id)
            .order_by(ExperimentRun.run_index)
        )
        return list(result.scalars().all())

    async def get_by_experiment_and_seed(
        self, experiment_id: UUID, seed: int
    ) -> Optional[ExperimentRun]:
        """Get specific run by experiment and seed."""
        result = await self.session.execute(
            select(ExperimentRun).where(
                ExperimentRun.experiment_id == experiment_id,
                ExperimentRun.seed == seed,
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_runs(self, experiment_id: UUID) -> List[ExperimentRun]:
        """Get pending runs for an experiment."""
        result = await self.session.execute(
            select(ExperimentRun).where(
                ExperimentRun.experiment_id == experiment_id,
                ExperimentRun.status.in_([ExperimentStatus.QUEUED, ExperimentStatus.RUNNING]),
            ).order_by(ExperimentRun.run_index)
        )
        return list(result.scalars().all())


class ExperimentResultRepository(BaseRepository[ExperimentResult]):
    """Repository for experiment result operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ExperimentResult)

    async def get_by_experiment(self, experiment_id: UUID) -> Optional[ExperimentResult]:
        """Get result for an experiment."""
        result = await self.session.execute(
            select(ExperimentResult).where(ExperimentResult.experiment_id == experiment_id)
        )
        return result.scalar_one_or_none()
