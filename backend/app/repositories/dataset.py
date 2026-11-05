"""Dataset repository for data access."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """Repository for dataset operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Dataset)

    async def get_by_dataset_id(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by dataset_id."""
        result = await self.session.execute(
            select(Dataset).where(Dataset.dataset_id == dataset_id)
        )
        return result.scalar_one_or_none()

    async def get_active(self, task_type: Optional[str] = None) -> List[Dataset]:
        """Get active datasets, optionally filtered by task type."""
        query = select(Dataset).where(Dataset.is_active == True)
        if task_type:
            query = query.where(Dataset.task_type == task_type)
        result = await self.session.execute(query.order_by(Dataset.name))
        return list(result.scalars().all())

    async def seed_default_datasets(self) -> List[Dataset]:
        """Seed default datasets if they don't exist."""
        defaults = [
            {
                "dataset_id": "iris",
                "name": "Iris Dataset",
                "description": "Classic iris flower classification dataset (150 samples, 4 features, 3 classes).",
                "task_type": "classification",
                "sample_count": 150,
                "feature_count": 4,
                "license": "CC-BY-4.0",
                "tags": ["tabular", "benchmark", "classification"],
                "feature_names": ["sepal_length", "sepal_width", "petal_length", "petal_width"],
                "target_name": "species",
                "class_names": ["setosa", "versicolor", "virginica"],
            },
            {
                "dataset_id": "german-credit",
                "name": "German Credit Benchmark",
                "description": "Statlog German Credit dataset evaluating creditworthiness risks.",
                "task_type": "classification",
                "sample_count": 1000,
                "feature_count": 20,
                "license": "CC-BY-4.0",
                "tags": ["tabular", "finance", "credit-risk"],
                "feature_names": [f"feature_{i}" for i in range(20)],
                "target_name": "credit_risk",
                "class_names": ["good", "bad"],
            },
        ]

        created = []
        for data in defaults:
            existing = await self.get_by_dataset_id(data["dataset_id"])
            if not existing:
                created.append(await self.create(**data))
        return created