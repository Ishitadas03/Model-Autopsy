"""Dataset database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

if TYPE_CHECKING:
    from app.models.experiment import Experiment
    from app.models.model_adapter import ModelAdapter


class Dataset(Base):
    """Benchmark dataset registered in the system."""

    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    dataset_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )  # e.g., "german-credit", "iris"
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)  # classification, regression
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False)
    license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # JSON list of tags
    feature_names: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # JSON list of feature names
    target_name: Mapped[str] = mapped_column(String(100), nullable=False)
    class_names: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # For classification
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)  # Additional metadata
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment",
        back_populates="dataset",
        primaryjoin="Dataset.dataset_id == foreign(Experiment.dataset_id)",
    )
    model_adapters: Mapped[list["ModelAdapter"]] = relationship(
        "ModelAdapter", back_populates="dataset"
    )

    __table_args__ = (
        Index("ix_datasets_task_active", "task_type", "is_active"),
    )
