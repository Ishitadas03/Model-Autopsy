"""Model adapter repository for data access."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.model_adapter import ModelAdapter
from backend.app.repositories.base import BaseRepository


class ModelAdapterRepository(BaseRepository[ModelAdapter]):
    """Repository for model adapter operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ModelAdapter)

    async def get_by_model_id(self, model_id: str) -> Optional[ModelAdapter]:
        """Get model adapter by model_id."""
        result = await self.session.execute(
            select(ModelAdapter).where(ModelAdapter.model_id == model_id)
        )
        return result.scalar_one_or_none()

    async def get_by_dataset(self, dataset_id: str, active_only: bool = True) -> List[ModelAdapter]:
        """Get model adapters for a dataset."""
        query = select(ModelAdapter).where(ModelAdapter.dataset_id == dataset_id)
        if active_only:
            query = query.where(ModelAdapter.is_active == True)
        result = await self.session.execute(query.order_by(ModelAdapter.name))
        return list(result.scalars().all())

    async def get_active(self, task_type: Optional[str] = None) -> List[ModelAdapter]:
        """Get active model adapters, optionally filtered by task type."""
        query = select(ModelAdapter).where(ModelAdapter.is_active == True)
        if task_type:
            query = query.where(ModelAdapter.task_type == task_type)
        result = await self.session.execute(query.order_by(ModelAdapter.name))
        return list(result.scalars().all())

    async def seed_default_adapters(self) -> List[ModelAdapter]:
        """Seed default model adapters if they don't exist."""
        defaults = [
            {
                "model_id": "rf-iris",
                "name": "Random Forest (Iris)",
                "description": "Standard Random Forest classifier for Iris dataset.",
                "task_type": "classification",
                "dataset_id": "iris",
                "framework": "scikit-learn",
                "model_class": "sklearn.ensemble.RandomForestClassifier",
                "hyperparameters": {"n_estimators": 100, "random_state": 42},
                "baseline_f1": 0.96,
                "baseline_accuracy": 0.96,
                "supported_corruptions": ["gaussian_noise", "mcar_missingness", "outlier_contamination"],
            },
            {
                "model_id": "lr-iris",
                "name": "Logistic Regression (Iris)",
                "description": "Logistic Regression classifier for Iris dataset.",
                "task_type": "classification",
                "dataset_id": "iris",
                "framework": "scikit-learn",
                "model_class": "sklearn.linear_model.LogisticRegression",
                "hyperparameters": {"max_iter": 200, "random_state": 42},
                "baseline_f1": 0.97,
                "baseline_accuracy": 0.97,
                "supported_corruptions": ["gaussian_noise", "mcar_missingness", "outlier_contamination"],
            },
            {
                "model_id": "gb-iris",
                "name": "Gradient Boosting (Iris)",
                "description": "Gradient Boosted Decision Trees for Iris dataset.",
                "task_type": "classification",
                "dataset_id": "iris",
                "framework": "scikit-learn",
                "model_class": "sklearn.ensemble.GradientBoostingClassifier",
                "hyperparameters": {"n_estimators": 100, "random_state": 42},
                "baseline_f1": 0.97,
                "baseline_accuracy": 0.97,
                "supported_corruptions": ["gaussian_noise", "mcar_missingness", "outlier_contamination"],
            },
            {
                "model_id": "rf-german-credit",
                "name": "RandomForest-v2 (Credit)",
                "description": "Standard ensemble classifier trained on German Credit tabular features.",
                "task_type": "classification",
                "dataset_id": "german-credit",
                "framework": "scikit-learn",
                "model_class": "sklearn.ensemble.RandomForestClassifier",
                "hyperparameters": {"n_estimators": 200, "random_state": 42},
                "baseline_f1": 0.958,
                "baseline_accuracy": 0.85,
                "supported_corruptions": ["gaussian_noise", "mcar_missingness", "outlier_contamination"],
            },
        ]

        created = []
        for data in defaults:
            existing = await self.get_by_model_id(data["model_id"])
            if not existing:
                created.append(await self.create(**data))
        return created