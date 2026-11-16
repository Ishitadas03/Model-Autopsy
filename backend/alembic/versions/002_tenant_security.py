"""Tenant ownership, benchmark visibility and scientifically nullable measurements.

Revision ID: 002_tenant_security
Revises: 001_initial_tables

Legacy records have no reliable owner mapping. They remain private/quarantined;
only explicitly known public benchmark datasets are published. Never guess ownership.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_tenant_security"
down_revision = "001_initial_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("datasets", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("datasets", sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_index("ix_datasets_owner_id", "datasets", ["owner_id"])
    op.add_column("experiments", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_experiments_owner_id", "experiments", ["owner_id"])
    # Existing benchmark datasets are public; uploaded/legacy custom datasets never are.
    op.execute(
        "UPDATE datasets SET is_public = true "
        "WHERE dataset_id IN ('iris', 'german-credit', 'german_credit') "
        "AND (tags IS NULL OR NOT (tags::jsonb ? 'user-upload'))"
    )
    op.alter_column("failed_samples", "confidence", existing_type=sa.Float(), nullable=True)
    op.add_column("experiment_results", sa.Column("baseline_metrics", sa.JSON(), nullable=True))
    op.add_column("experiment_results", sa.Column("worst_case_metrics", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("experiment_results", "worst_case_metrics")
    op.drop_column("experiment_results", "baseline_metrics")
    op.alter_column("failed_samples", "confidence", existing_type=sa.Float(), nullable=False)
    op.drop_index("ix_experiments_owner_id", table_name="experiments")
    op.drop_column("experiments", "owner_id")
    op.drop_index("ix_datasets_owner_id", table_name="datasets")
    op.drop_column("datasets", "is_public")
    op.drop_column("datasets", "owner_id")
