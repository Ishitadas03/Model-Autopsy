"""Initial schema migration: create all tables with indexes.

Revision ID: 001_initial_tables
Revises: 
Create Date: 2026-10-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. datasets
    op.create_table(
        "datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("sample_count", sa.Integer(), nullable=False),
        sa.Column("feature_count", sa.Integer(), nullable=False),
        sa.Column("license", sa.String(100), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("feature_names", sa.JSON(), nullable=False),
        sa.Column("target_name", sa.String(100), nullable=False),
        sa.Column("class_names", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_datasets_dataset_id", "datasets", ["dataset_id"])
    op.create_index("ix_datasets_task_active", "datasets", ["task_type", "is_active"])

    # 2. model_adapters
    op.create_table(
        "model_adapters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("model_id", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("dataset_id", sa.String(100), sa.ForeignKey("datasets.dataset_id"), nullable=False),
        sa.Column("framework", sa.String(100), nullable=False),
        sa.Column("model_class", sa.String(200), nullable=False),
        sa.Column("hyperparameters", sa.JSON(), nullable=False),
        sa.Column("baseline_f1", sa.Float(), nullable=True),
        sa.Column("baseline_accuracy", sa.Float(), nullable=True),
        sa.Column("supported_corruptions", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_model_adapters_model_id", "model_adapters", ["model_id"])
    op.create_index("ix_model_adapters_dataset_id", "model_adapters", ["dataset_id"])
    op.create_index("ix_model_adapters_dataset_active", "model_adapters", ["dataset_id", "is_active"])
    op.create_index("ix_model_adapters_task_active", "model_adapters", ["task_type", "is_active"])

    # 3. experiments
    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", sa.String(50), nullable=False, unique=True),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("dataset_name", sa.String(200), nullable=False),
        sa.Column("dataset_id", sa.String(100), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("perturbation_family", sa.String(50), nullable=False),
        sa.Column("noise_type", sa.String(100), nullable=False),
        sa.Column("evaluation_metric", sa.String(50), nullable=False),
        sa.Column("failure_threshold", sa.Float(), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("stress_mode", sa.String(50), nullable=False, server_default="incremental"),
        sa.Column("severity_levels", sa.JSON(), nullable=False),
        sa.Column("seeds", sa.JSON(), nullable=False),
        sa.Column("config_yaml", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_seed_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_severity_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_experiments_experiment_id", "experiments", ["experiment_id"])
    op.create_index("ix_experiments_dataset_id", "experiments", ["dataset_id"])
    op.create_index("ix_experiments_status", "experiments", ["status"])
    op.create_index("ix_experiments_status_created", "experiments", ["status", "created_at"])
    op.create_index("ix_experiments_dataset_model", "experiments", ["dataset_id", "model_name"])

    # 4. experiment_runs
    op.create_table(
        "experiment_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("run_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_severity", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("experiment_id", "seed", name="uq_experiment_run_seed"),
    )
    op.create_index("ix_experiment_runs_experiment_status", "experiment_runs", ["experiment_id", "status"])

    # 5. experiment_results
    op.create_table(
        "experiment_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("baseline_macro_f1", sa.Float(), nullable=True),
        sa.Column("baseline_accuracy", sa.Float(), nullable=True),
        sa.Column("baseline_per_class", sa.JSON(), nullable=True),
        sa.Column("worst_case_macro_f1", sa.Float(), nullable=True),
        sa.Column("worst_case_accuracy", sa.Float(), nullable=True),
        sa.Column("worst_case_severity", sa.Float(), nullable=True),
        sa.Column("observed_boundary", sa.Float(), nullable=True),
        sa.Column("boundary_caveat", sa.String(500), nullable=False, server_default="Observed failure boundary under the specified experimental configuration."),
        sa.Column("curve_data", sa.JSON(), nullable=False),
        sa.Column("feature_vulnerabilities", sa.JSON(), nullable=False),
        sa.Column("metric_statistics", sa.JSON(), nullable=True),
        sa.Column("statistical_validation", sa.JSON(), nullable=True),
        sa.Column("failed_samples_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consensus_failures", sa.JSON(), nullable=True),
        sa.Column("error_persistence_rate", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # 6. failed_samples
    op.create_table(
        "failed_samples",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sample_index", sa.Integer(), nullable=False),
        sa.Column("sample_id", sa.String(100), nullable=False),
        sa.Column("true_label", sa.String(100), nullable=False),
        sa.Column("predicted_label", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("noise_level", sa.Float(), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("features_clean", sa.JSON(), nullable=False),
        sa.Column("features_stressed", sa.JSON(), nullable=False),
        sa.Column("feature_diffs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_failed_samples_experiment_id", "failed_samples", ["experiment_id"])
    op.create_index("ix_failed_samples_experiment_noise", "failed_samples", ["experiment_id", "noise_level"])
    op.create_index("ix_failed_samples_experiment_label", "failed_samples", ["experiment_id", "true_label"])
    op.create_index("ix_failed_samples_experiment_seed", "failed_samples", ["experiment_id", "seed"])

    # 7. artifact_manifests
    op.create_table(
        "artifact_manifests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_type", sa.String(50), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(200), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_artifact_manifests_experiment_id", "artifact_manifests", ["experiment_id"])
    op.create_index("ix_artifact_manifests_experiment_type", "artifact_manifests", ["experiment_id", "artifact_type"])
    op.create_index("ix_artifact_manifests_experiment_seed", "artifact_manifests", ["experiment_id", "seed"])

    # 8. artifact_references
    op.create_table(
        "artifact_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("manifest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifact_manifests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference_type", sa.String(50), nullable=False),
        sa.Column("reference_url", sa.String(500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_artifact_references_manifest_id", "artifact_references", ["manifest_id"])


def downgrade() -> None:
    op.drop_table("artifact_references")
    op.drop_table("artifact_manifests")
    op.drop_table("failed_samples")
    op.drop_table("experiment_results")
    op.drop_table("experiment_runs")
    op.drop_table("experiments")
    op.drop_table("model_adapters")
    op.drop_table("datasets")
