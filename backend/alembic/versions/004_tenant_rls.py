"""Supabase PostgREST tenant read isolation; deny direct writes by default.

Revision ID: 004_tenant_rls
Revises: 003_durable_jobs

This migration intentionally ABORTS if pre-existing policies are found. RLS
policies are additive (OR), so silently installing our SELECT policies beside
an old permissive policy would NOT secure the table.

The FastAPI backend uses its private PostgreSQL connection and checks
ownership itself; this migration protects direct Supabase authenticated/anon
roles from cross-user reads or writes. Test privileges in staging first.
"""
from alembic import op
import sqlalchemy as sa

revision = "004_tenant_rls"
down_revision = "003_durable_jobs"
branch_labels = None
depends_on = None

_TABLES = (
    "datasets", "model_adapters", "experiments", "experiment_runs",
    "experiment_results", "failed_samples",
    "artifact_manifests", "artifact_references",
)

_READ_POLICIES = {
    "datasets": (
        "datasets_tenant_read",
        "(owner_id = auth.uid() OR (is_public IS TRUE AND owner_id IS NULL))",
    ),
    "experiments": (
        "experiments_tenant_read",
        "(owner_id IS NOT NULL AND owner_id = auth.uid())",
    ),
    "model_adapters": (
        "models_visible_dataset_read",
        """EXISTS (
            SELECT 1 FROM public.datasets AS d
            WHERE d.dataset_id = model_adapters.dataset_id
            AND (d.owner_id = auth.uid() OR (d.is_public IS TRUE AND d.owner_id IS NULL))
        )""",
    ),
    "experiment_runs": (
        "runs_owned_experiment_read",
        """EXISTS (
            SELECT 1 FROM public.experiments AS e
            WHERE e.id = experiment_runs.experiment_id
            AND e.owner_id IS NOT NULL AND e.owner_id = auth.uid()
        )""",
    ),
    "experiment_results": (
        "results_owned_experiment_read",
        """EXISTS (
            SELECT 1 FROM public.experiments AS e
            WHERE e.id = experiment_results.experiment_id
            AND e.owner_id IS NOT NULL AND e.owner_id = auth.uid()
        )""",
    ),
    "failed_samples": (
        "failures_owned_experiment_read",
        """EXISTS (
            SELECT 1 FROM public.experiments AS e
            WHERE e.id = failed_samples.experiment_id
            AND e.owner_id IS NOT NULL AND e.owner_id = auth.uid()
        )""",
    ),
    "artifact_manifests": (
        "artifacts_owned_experiment_read",
        """EXISTS (
            SELECT 1 FROM public.experiments AS e
            WHERE e.id = artifact_manifests.experiment_id
            AND e.owner_id IS NOT NULL AND e.owner_id = auth.uid()
        )""",
    ),
    "artifact_references": (
        "artifact_refs_owned_experiment_read",
        """EXISTS (
            SELECT 1 FROM public.artifact_manifests AS m
            JOIN public.experiments AS e ON e.id = m.experiment_id
            WHERE m.id = artifact_references.manifest_id
            AND e.owner_id IS NOT NULL AND e.owner_id = auth.uid()
        )""",
    ),
}


def upgrade() -> None:
    bind = op.get_bind()
    # Refuse to weaken existing RLS policies, including permissive legacy ones.
    # The policy inventory must be assessed and reconciled by an operator.
    rows = bind.execute(
        sa.text("""
            SELECT tablename, policyname
            FROM pg_catalog.pg_policies
            WHERE schemaname = 'public' AND tablename = ANY(:tables)
        """),
        {"tables": list(_TABLES)},
    ).fetchall()
    if rows:
        found = ", ".join(f"{t}.{p}" for t, p in rows)
        raise RuntimeError(
            "RLS migration blocked by existing policies: " + found +
            ". Review, back up and reconcile policies in staging first."
        )

    # Ensure auth.uid() is present rather than deploying incomplete protection.
    valid = bind.execute(
        sa.text("SELECT to_regprocedure('auth.uid()') IS NOT NULL")
    ).scalar_one()
    if not valid:
        raise RuntimeError("Supabase auth.uid() not available; refusing migration")

    for table in _TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
        # No policies for INSERT/UPDATE/DELETE: PostgREST clients cannot write.
        # Backend-only SQL writes are handled by its privileged DB role.
        name, expression = _READ_POLICIES[table]
        op.execute(
            f"CREATE POLICY {name} ON public.{table} "
            f"AS PERMISSIVE FOR SELECT TO authenticated "
            f"USING ({expression})"
        )


def downgrade() -> None:
    # A rollback must not leave a tenant data breach by disabling RLS.
    # No automatic downgrade: restore under controlled DBA review only.
    raise RuntimeError(
        "Security downgrade blocked: manually review and preserve RLS protection."
    )
