"""Persist worker queue metadata and result metrics.

Revision ID: 003_durable_jobs
Revises: 002_tenant_security
"""
from alembic import op
import sqlalchemy as sa

revision = "003_durable_jobs"
down_revision = "002_tenant_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("experiments", sa.Column("execution_payload", sa.JSON(), nullable=True))
    op.add_column("experiments", sa.Column("lease_owner", sa.String(100), nullable=True))
    op.add_column("experiments", sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("experiments", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_experiments_pending_claim", "experiments", ["status", "created_at"])
    op.create_index("ix_experiments_expired_lease", "experiments", ["status", "lease_expires_at"])
    # Legacy jobs did not capture the full request configuration and therefore
    # cannot be replayed safely: do not fill their execution_payload.


def downgrade() -> None:
    op.drop_index("ix_experiments_expired_lease", table_name="experiments")
    op.drop_index("ix_experiments_pending_claim", table_name="experiments")
    op.drop_column("experiments", "attempt_count")
    op.drop_column("experiments", "lease_expires_at")
    op.drop_column("experiments", "lease_owner")
    op.drop_column("experiments", "execution_payload")
