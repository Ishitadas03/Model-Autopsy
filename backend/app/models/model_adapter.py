"""Model Adapter database model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.experiment import Experiment


class ModelAdapter(Base):
    """Model adapter configuration registered in the system."""

    __tablename__ = "model_adapters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )  # e.g., "rf-german-credit"
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("datasets.dataset_id"), nullable=False, index=True
    )
    framework: Mapped[str] = mapped_column(String(100), nullable=False)  # scikit-learn, pytorch, etc.
    model_class: Mapped[str] = mapped_column(String(200), nullable=False)  # Full class path
    hyperparameters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # JSON dict
    baseline_f1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    baseline_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    supported_corruptions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # List of stress types
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="model_adapters")
    experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment",
        back_populates="model_adapter",
        primaryjoin="ModelAdapter.model_id == foreign(Experiment.model_name)",
    )

    __table_args__ = (
        Index("ix_model_adapters_dataset_active", "dataset_id", "is_active"),
        Index("ix_model_adapters_task_active", "task_type", "is_active"),
    )
