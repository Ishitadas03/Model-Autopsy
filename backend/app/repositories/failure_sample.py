"""Failed sample repository for data access."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.failure_sample import FailedSample
from app.repositories.base import BaseRepository


class FailureSampleRepository(BaseRepository[FailedSample]):
    """Repository for failed sample operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, FailedSample)

    async def get_by_experiment(
        self,
        experiment_id: UUID,
        page: int = 1,
        page_size: int = 20,
        filter_class: Optional[str] = None,
    ) -> tuple[List[FailedSample], int]:
        """Get failed samples for an experiment with pagination."""
        query = select(FailedSample).where(FailedSample.experiment_id == experiment_id)
        count_query = select(func.count()).select_from(FailedSample).where(
            FailedSample.experiment_id == experiment_id
        )

        if filter_class and filter_class != "All":
            query = query.where(
                (FailedSample.true_label == filter_class) | (FailedSample.predicted_label == filter_class)
            )
            count_query = count_query.where(
                (FailedSample.true_label == filter_class) | (FailedSample.predicted_label == filter_class)
            )

        # Get total count
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results
        query = query.order_by(FailedSample.noise_level.desc(), FailedSample.sample_index).offset(
            (page - 1) * page_size
        ).limit(page_size)

        result = await self.session.execute(query)
        samples = list(result.scalars().all())

        return samples, total

    async def get_by_experiment_and_noise_level(
        self, experiment_id: UUID, noise_level: float
    ) -> List[FailedSample]:
        """Get failed samples for a specific noise level."""
        result = await self.session.execute(
            select(FailedSample)
            .where(
                FailedSample.experiment_id == experiment_id,
                FailedSample.noise_level == noise_level,
            )
            .order_by(FailedSample.sample_index)
        )
        return list(result.scalars().all())

    async def get_failure_stats(self, experiment_id: UUID) -> dict:
        """Get failure statistics for an experiment."""
        # Total failures
        total_result = await self.session.execute(
            select(func.count()).select_from(FailedSample).where(
                FailedSample.experiment_id == experiment_id
            )
        )
        total = total_result.scalar_one()

        # By noise level
        by_noise_result = await self.session.execute(
            select(FailedSample.noise_level, func.count())
            .where(FailedSample.experiment_id == experiment_id)
            .group_by(FailedSample.noise_level)
            .order_by(FailedSample.noise_level)
        )
        by_noise = {float(noise): count for noise, count in by_noise_result.all()}

        # By true label
        by_label_result = await self.session.execute(
            select(FailedSample.true_label, func.count())
            .where(FailedSample.experiment_id == experiment_id)
            .group_by(FailedSample.true_label)
        )
        by_label = {label: count for label, count in by_label_result.all()}

        return {
            "total": total,
            "by_noise_level": by_noise,
            "by_true_label": by_label,
        }