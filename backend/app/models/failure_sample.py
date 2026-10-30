"""Failed sample SQLAlchemy models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.experiment import Experiment


class FailedSample(Base):
    """Failed sample model - individual misclassified instances under stress."""

    __tablename__ = "failed_samples"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sample_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Index in test set
    sample_id: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "samp-101"
    true_label: Mapped[str] = mapped_column(String(100), nullable=False)
    predicted_label: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    noise_level: Mapped[float] = mapped_column(Float, nullable=False)  # Severity level
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    features_clean: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # {feature: value}
    features_stressed: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # {feature: value}
    feature_diffs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # {feature: diff}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="failed_samples")

    __table_args__ = (
        Index("ix_failed_samples_experiment_noise", "experiment_id", "noise_level"),
        Index("ix_failed_samples_experiment_label", "experiment_id", "true_label"),
        Index("ix_failed_samples_experiment_seed", "experiment_id", "seed"),
    )