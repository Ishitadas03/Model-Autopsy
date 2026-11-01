"""Artifact repository for data access."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.artifact import ArtifactManifest, ArtifactReference, ArtifactType
from backend.app.repositories.base import BaseRepository


class ArtifactRepository(BaseRepository[ArtifactManifest]):
    """Repository for artifact operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ArtifactManifest)

    async def get_by_experiment(
        self, experiment_id: UUID, artifact_type: Optional[ArtifactType] = None
    ) -> List[ArtifactManifest]:
        """Get all artifacts for an experiment."""
        query = select(ArtifactManifest).where(ArtifactManifest.experiment_id == experiment_id)
        if artifact_type:
            query = query.where(ArtifactManifest.artifact_type == artifact_type)
        query = query.order_by(ArtifactManifest.seed.nulls_first(), ArtifactManifest.artifact_type)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_experiment_and_type(
        self, experiment_id: UUID, artifact_type: ArtifactType, seed: Optional[int] = None
    ) -> Optional[ArtifactManifest]:
        """Get specific artifact for an experiment."""
        query = select(ArtifactManifest).where(
            ArtifactManifest.experiment_id == experiment_id,
            ArtifactManifest.artifact_type == artifact_type,
        )
        if seed is not None:
            query = query.where(ArtifactManifest.seed == seed)
        else:
            query = query.where(ArtifactManifest.seed.is_(None))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_references(self, manifest_id: UUID) -> Optional[ArtifactManifest]:
        """Get artifact manifest with references loaded."""
        result = await self.session.execute(
            select(ArtifactManifest)
            .options(selectinload(ArtifactManifest.references))
            .where(ArtifactManifest.id == manifest_id)
        )
        return result.scalar_one_or_none()


class ArtifactReferenceRepository(BaseRepository[ArtifactReference]):
    """Repository for artifact reference operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ArtifactReference)

    async def get_by_manifest(self, manifest_id: UUID) -> List[ArtifactReference]:
        """Get all references for a manifest."""
        result = await self.session.execute(
            select(ArtifactReference).where(ArtifactReference.manifest_id == manifest_id)
        )
        return list(result.scalars().all())