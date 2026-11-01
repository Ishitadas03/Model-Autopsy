"""Base repository class for async database operations."""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from backend.app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic base repository for CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id_) -> Optional[ModelType]:
        """Get a single record by primary key."""
        result = await self.session.execute(select(self.model).where(self.model.id == id_))
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, order_by: str = "created_at"
    ) -> List[ModelType]:
        """Get all records with pagination."""
        order_column = getattr(self.model, order_by, self.model.created_at)
        result = await self.session.execute(
            select(self.model).order_by(order_column.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        """Update an existing record."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete a record."""
        await self.session.delete(instance)
        await self.session.flush()

    async def count(self) -> int:
        """Count total records."""
        from sqlalchemy import func
        result = await self.session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()

    async def exists(self, **filters) -> bool:
        """Check if record exists with given filters."""
        from sqlalchemy import func
        query = select(func.count()).select_from(self.model)
        for key, value in filters.items():
            query = query.where(getattr(self.model, key) == value)
        result = await self.session.execute(query)
        return result.scalar_one() > 0