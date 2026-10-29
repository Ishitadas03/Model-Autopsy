"""Experiment SQLAlchemy models."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.models.dataset import Dataset
    from backend.app.models.model_adapter import ModelAdapter
    from backend.app.models.failure_sample import FailedSample
    from backend.app.models.artifact import ArtifactManifest, ArtifactReference


class ExperimentStatus(str, enum.Enum):
    """Experiment status enumeration."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    """Task type enumeration."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"


class StressType(str, enum.Enum):
    """Stress/corruption type enumeration."""

    GAUSSIAN_NOISE = "gaussian_noise"
    MCAR_MISSINGNESS = "mcar_missingness"
    OUTLIER_CONTAMINATION = "outlier_contamination"


class StressMode(str, enum.Enum):
    """Stress application mode enumeration."""

    INCREMENTAL = "incremental"
    INDEPENDENT = "independent"


class Experiment(Base):
    """Experiment model - represents a stress testing experiment configuration."""

    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )  # e.g., "EXP-0241"
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType), nullable=False)
    perturbation_family: Mapped[StressType] = mapped_column(Enum(StressType), nullable=False)
    noise_type: Mapped[str] = mapped_column(String(100), nullable=False)
    evaluation_metric: Mapped[str] = mapped_column(String(50), nullable=False)
    failure_threshold: Mapped[float] = mapped_column(nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    stress_mode: Mapped[StressMode] = mapped_column(Enum(StressMode), default=StressMode.INCREMENTAL)
    severity_levels: Mapped[list] = mapped_column(JSON, nullable=False)  # List of severity values
    seeds: Mapped[list] = mapped_column(JSON, nullable=False)  # List of seeds for multi-seed
    config_yaml: Mapped[str] = mapped_column(Text, nullable=False)  # Full YAML config
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), default=ExperimentStatus.QUEUED, nullable=False, index=True
    )
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_seed_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_severity_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="experiments")
    model_adapter: Mapped["ModelAdapter"] = relationship("ModelAdapter", back_populates="experiments")
    runs: Mapped[list["ExperimentRun"]] = relationship(
        "ExperimentRun", back_populates="experiment", cascade="all, delete-orphan"
    )
    result: Mapped[Optional["ExperimentResult"]] = relationship(
        "ExperimentResult", back_populates="experiment", cascade="all, delete-orphan", uselist=False
    )
    failed_samples: Mapped[list["FailedSample"]] = relationship(
        "FailedSample", back_populates="experiment", cascade="all, delete-orphan"
    )
    artifacts: Mapped[list["ArtifactManifest"]] = relationship(
        "ArtifactManifest", back_populates="experiment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_experiments_status_created", "status", "created_at"),
        Index("ix_experiments_dataset_model", "dataset_id", "model_name"),
    )


class ExperimentRun(Base):
    """Individual run of an experiment (per seed)."""

    __tablename__ = "experiment_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    run_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-based index in seeds list
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus), default=ExperimentStatus.QUEUED, nullable=False
    )
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_severity: Mapped[Optional[float]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="runs")

    __table_args__ = (
        UniqueConstraint("experiment_id", "seed", name="uq_experiment_run_seed"),
        Index("ix_experiment_runs_experiment_status", "experiment_id", "status"),
    )


class ExperimentResult(Base):
    """Aggregated experiment results across all seeds."""

    __tablename__ = "experiment_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Baseline metrics (clean data)
    baseline_macro_f1: Mapped[Optional[float]] = mapped_column(nullable=True)
    baseline_accuracy: Mapped[Optional[float]] = mapped_column(nullable=True)
    baseline_per_class: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Worst case metrics
    worst_case_macro_f1: Mapped[Optional[float]] = mapped_column(nullable=True)
    worst_case_accuracy: Mapped[Optional[float]] = mapped_column(nullable=True)
    worst_case_severity: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Failure boundary
    observed_boundary: Mapped[Optional[float]] = mapped_column(nullable=True)
    boundary_caveat: Mapped[str] = mapped_column(
        String(500), default="Observed failure boundary under the specified experimental configuration."
    )

    # Curve data (robustness curve)
    curve_data: Mapped[list] = mapped_column(JSON, nullable=False)  # List of {severity, macro_f1, accuracy, ...}

    # Feature vulnerabilities
    feature_vulnerabilities: Mapped[list] = mapped_column(JSON, nullable=False)  # List of {feature, drop, rank, caveat}

    # Statistical validation (multi-seed)
    metric_statistics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    statistical_validation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Failure patterns
    failed_samples_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consensus_failures: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    error_persistence_rate: Mapped[Optional[float]] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="result")