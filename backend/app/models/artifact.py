"""Artifact SQLAlchemy models."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.experiment import Experiment


class ArtifactType(str, enum.Enum):
    """Artifact type enumeration."""

    RESULTS_JSON = "results_json"
    CURVES_CSV = "curves_csv"
    REPORT_MD = "report_md"
    MANIFEST_JSON = "manifest_json"
    REPRODUCIBILITY_JSON = "reproducibility_json"


class ArtifactManifest(Base):
    """Artifact manifest - tracks all generated artifacts for an experiment."""

    __tablename__ = "artifact_manifests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    artifact_type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType), nullable=False)
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Null for aggregated artifacts
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # Relative to artifacts base dir
    file_name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata: Mapped[dict] = mapped_column(nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="artifacts")
    references: Mapped[list["ArtifactReference"]] = relationship(
        "ArtifactReference", back_populates="manifest", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_artifact_manifests_experiment_type", "experiment_id", "artifact_type"),
        Index("ix_artifact_manifests_experiment_seed", "experiment_id", "seed"),
    )


class ArtifactReference(Base):
    """Artifact reference - links artifacts to external storage or provides download URLs."""

    __tablename__ = "artifact_references"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    manifest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("artifact_manifests.id", ondelete="CASCADE"), nullable=False
    )
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)  # local, s3, gcs, etc.
    reference_url: Mapped[str] = mapped_column(String(500), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata: Mapped[dict] = mapped_column(nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    manifest: Mapped["ArtifactManifest"] = relationship("ArtifactManifest", back_populates="references")

    __table_args__ = (
        Index("ix_artifact_references_manifest", "manifest_id"),
    )