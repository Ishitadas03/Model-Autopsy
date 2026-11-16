"""Real PostgreSQL 17 migration/tenant-security acceptance test for GitHub Actions.

Runs in two phases: seed after Alembic 001, verify after upgrading to 004.
Never targets Supabase or a production database. Only executes against the
explicit local CI connection URL, with independent simulated JWT identities.
"""
from __future__ import annotations

import os
import sys
import uuid

import psycopg2
from psycopg2 import errors

OWN_A = "11111111-1111-4111-8111-111111111111"
OWN_B = "22222222-2222-4222-8222-222222222222"
DATA_PUBLIC = "iris"
DATA_LEGACY = "legacy-private"
DATA_A = "tenant-a"
DATA_B = "tenant-b"

def open_ci_db():
    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("postgresql+asyncpg://postgres:postgres@localhost:5432/model_autopsy_ci"):
        raise RuntimeError("Refusing RLS test outside the isolated local CI database")
    conn = psycopg2.connect(url.replace("postgresql+asyncpg://", "postgresql://", 1))
    conn.autocommit = True
    return conn


def insert_dataset(cursor, dataset_id, tags="[]"):
    cursor.execute(
        """INSERT INTO public.datasets
         (id, dataset_id, name, task_type, sample_count, feature_count,
          tags, feature_names, target_name, metadata)
         VALUES (%s, %s, %s, 'classification', 20, 1, %s::json, '["feature"]'::json,
                 'target', '{}'::json)""",
        (str(uuid.uuid4()), dataset_id, dataset_id, tags),
    )


def insert_experiment(cursor, name, dataset_id):
    internal = str(uuid.uuid4())
    cursor.execute(
        """INSERT INTO public.experiments
         (id, experiment_id, model_name, dataset_name, dataset_id, task_type,
          perturbation_family, noise_type, evaluation_metric, failure_threshold,
          seed, severity_levels, seeds, config_yaml)
         VALUES (%s, %s, 'RandomForest', 'CI dataset', %s, 'classification',
          'gaussian_noise', 'gaussian_noise', 'f1', 0.5, 42,
          '[0.0, 0.1]'::json, '[42]'::json, 'experiment: ci')""",
        (internal, name, dataset_id),
    )
    return internal


def seed():
    with open_ci_db() as conn, conn.cursor() as cursor:
        for id_, tags in [(DATA_PUBLIC, "[]"), (DATA_LEGACY, '["user-upload"]'),
                          (DATA_A, '["user-upload"]'), (DATA_B, '["user-upload"]')]:
            insert_dataset(cursor, id_, tags)
        old_id = insert_experiment(cursor, "EXP-LEGACY", DATA_LEGACY)
        cursor.execute(
            "INSERT INTO public.experiment_runs (id,experiment_id,seed,run_index) VALUES (%s,%s,42,0)",
            (str(uuid.uuid4()), old_id),
        )
        cursor.execute(
            """INSERT INTO public.artifact_manifests
               (id,experiment_id,artifact_type,file_path,file_name,
                file_size_bytes,content_hash,mime_type,metadata)
               VALUES (%s,%s,'report','ci/report.md','report.md',5,%s,
                       'text/markdown','{}'::json)""",
            (str(uuid.uuid4()), old_id, "a" * 64),
        )
        cursor.execute("SELECT count(*) FROM public.experiments")
        assert cursor.fetchone()[0] == 1
        print("Seeded small legacy records before upgrade 002-004")


def owner_read(cursor, role, user):
    cursor.execute("SAVEPOINT tenant_read_scope")
    cursor.execute(f"SET LOCAL ROLE {role}")
    if user:
        cursor.execute("SELECT set_config('request.jwt.claim.sub', %s, true)", (user,))
    cursor.execute(
        "SELECT dataset_id FROM public.datasets ORDER BY dataset_id"
    )
    ids = {r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT experiment_id FROM public.experiments ORDER BY experiment_id")
    experiments = {r[0] for r in cursor.fetchall()}
    cursor.execute("SELECT count(*) FROM public.experiment_runs")
    runs = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM public.artifact_manifests")
    artifacts = cursor.fetchone()[0]
    cursor.execute("ROLLBACK TO SAVEPOINT tenant_read_scope")
    cursor.execute("RELEASE SAVEPOINT tenant_read_scope")
    return ids, experiments, runs, artifacts


def verify():
    with open_ci_db() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT version_num FROM public.alembic_version")
        assert cursor.fetchone()[0] == "004_tenant_rls"
        cursor.execute(
            "SELECT dataset_id,is_public,owner_id FROM public.datasets ORDER BY dataset_id"
        )
        data = {id_: (is_public, owner) for id_, is_public, owner in cursor.fetchall()}
        assert data[DATA_PUBLIC] == (True, None)
        assert data[DATA_LEGACY] == (False, None)
        assert len(data) == 4
        cursor.execute("SELECT experiment_id,owner_id FROM public.experiments")
        assert cursor.fetchall() == [("EXP-LEGACY", None)]

        cursor.execute(
            "UPDATE public.datasets SET owner_id=%s WHERE dataset_id=%s", (OWN_A, DATA_A)
        )
        cursor.execute(
            "UPDATE public.datasets SET owner_id=%s WHERE dataset_id=%s", (OWN_B, DATA_B)
        )
        a_id = insert_experiment(cursor, "EXP-TENANT-A", DATA_A)
        b_id = insert_experiment(cursor, "EXP-TENANT-B", DATA_B)
        cursor.execute(
            "UPDATE public.experiments SET owner_id=%s WHERE id=%s", (OWN_A, a_id)
        )
        cursor.execute(
            "UPDATE public.experiments SET owner_id=%s WHERE id=%s", (OWN_B, b_id)
        )
        cursor.execute(
            "INSERT INTO public.experiment_runs(id,experiment_id,seed,run_index) VALUES(%s,%s,42,0)",
            (str(uuid.uuid4()), a_id),
        )
        cursor.execute(
            """INSERT INTO public.experiment_results
            (id,experiment_id,curve_data,feature_vulnerabilities)
            VALUES(%s,%s,'[]'::json,'[]'::json)""",
            (str(uuid.uuid4()), a_id),
        )
        cursor.execute(
            """INSERT INTO public.artifact_manifests
            (id,experiment_id,artifact_type,file_path,file_name,file_size_bytes,
             content_hash,mime_type,metadata)
            VALUES (%s,%s,'report','ci/tA.md','tA.md',1,%s,'text/markdown','{}'::json)""",
            (str(uuid.uuid4()), a_id, "b" * 64),
        )
        cursor.execute(
            "GRANT USAGE ON SCHEMA public TO authenticated, anon"
        )
        cursor.execute(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated, anon"
        )
        cursor.execute(
            "SELECT relname,relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND relname IN ('datasets','experiments','experiment_runs','experiment_results','failed_samples','artifact_manifests','artifact_references','model_adapters')"
        )
        assert len(cursor.fetchall()) == 8

        ids_a, exps_a, runs_a, arts_a = owner_read(cursor, "authenticated", OWN_A)
        assert ids_a == {DATA_PUBLIC, DATA_A}, ids_a
        assert exps_a == {"EXP-TENANT-A"}, exps_a
        assert runs_a == 1 and arts_a == 1, (runs_a, arts_a)
        ids_b, exps_b, runs_b, arts_b = owner_read(cursor, "authenticated", OWN_B)
        assert ids_b == {DATA_PUBLIC, DATA_B}, ids_b
        assert exps_b == {"EXP-TENANT-B"}, exps_b
        assert runs_b == 0 and arts_b == 0, (runs_b, arts_b)
        ids_anon, exps_anon, runs_anon, arts_anon = owner_read(cursor, "anon", None)
        assert not ids_anon and not exps_anon and not runs_anon and not arts_anon

        cursor.execute("SAVEPOINT owner_write_scope")
        cursor.execute("SET LOCAL ROLE authenticated")
        cursor.execute(
            "SELECT set_config('request.jwt.claim.sub', %s, true)", (OWN_A,)
        )
        cursor.execute("SAVEPOINT before_write")
        try:
            cursor.execute("UPDATE public.experiments SET progress_percent=77 WHERE experiment_id='EXP-TENANT-A'")
        except psycopg2.Error as exc:
            # PostgreSQL can reject UPDATE outright, depending on privileges.
            assert exc.pgcode in ("42501", "44000"), exc
            cursor.execute("ROLLBACK TO SAVEPOINT before_write")
        else:
            # With table-level UPDATE privilege but no RLS UPDATE policy,
            # PostgreSQL may instead silently affect zero rows.
            assert cursor.rowcount == 0, "A direct user update bypassed RLS"
        cursor.execute("ROLLBACK TO SAVEPOINT owner_write_scope")
        cursor.execute("RELEASE SAVEPOINT owner_write_scope")

        cursor.execute(
            "SELECT has_function_privilege('anon','public.rls_auto_enable()','EXECUTE')"
        )
        assert cursor.fetchone()[0] is False
        cursor.execute(
            "SELECT has_function_privilege('authenticated','public.rls_auto_enable()','EXECUTE')"
        )
        assert cursor.fetchone()[0] is False
        print("PostgreSQL migration + two-tenant RLS checks passed; legacy rows retained")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("seed", "verify"):
        raise SystemExit("Usage: postgres_rls_acceptance.py seed|verify")
    globals()[sys.argv[1]]()
