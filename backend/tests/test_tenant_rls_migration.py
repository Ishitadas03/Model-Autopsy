"""Validate tenant RLS migration never merges with unsafe policies or disables RLS.

These are source-level tests. A staging Supabase Postgres security test with
two authenticated identities remains required before production rollout.
"""
import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def migration():
    file = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "004_tenant_rls.py"
    spec = importlib.util.spec_from_file_location("tenant_rls_migration", file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResult:
    def __init__(self, value):
        self.value = value

    def fetchall(self):
        return self.value

    def scalar_one(self):
        return self.value


class FakeBind:
    def __init__(self, policies=None, has_auth_uid=True):
        self.policies = policies or []
        self.has_auth_uid = has_auth_uid

    def execute(self, statement, params=None):
        sql = str(statement)
        if "pg_catalog.pg_policies" in sql:
            return FakeResult(self.policies)
        if "to_regprocedure" in sql:
            return FakeResult(self.has_auth_uid)
        raise AssertionError(f"Unexpected database query: {sql}")


def test_rls_migration_refuses_any_existing_policy(monkeypatch, migration):
    statements = []
    monkeypatch.setattr(migration.op, "get_bind", lambda: FakeBind([("datasets", "old_allow_all")]))
    monkeypatch.setattr(migration.op, "execute", statements.append)
    with pytest.raises(RuntimeError, match="existing policies"):
        migration.upgrade()
    assert statements == []


def test_rls_migration_refuses_missing_supabase_identity_function(monkeypatch, migration):
    statements = []
    monkeypatch.setattr(migration.op, "get_bind", lambda: FakeBind(has_auth_uid=False))
    monkeypatch.setattr(migration.op, "execute", statements.append)
    with pytest.raises(RuntimeError, match="auth.uid"):
        migration.upgrade()
    assert statements == []


def test_rls_migration_protects_every_tenant_table(monkeypatch, migration):
    statements = []
    monkeypatch.setattr(migration.op, "get_bind", lambda: FakeBind())
    monkeypatch.setattr(migration.op, "execute", statements.append)
    migration.upgrade()
    enables = [sql for sql in statements if "ENABLE ROW LEVEL SECURITY" in sql]
    policies = [sql for sql in statements if "CREATE POLICY" in sql]
    assert len(enables) == len(migration._TABLES) == 8
    assert len(policies) == 8
    assert all("FOR SELECT TO authenticated" in sql for sql in policies)
    assert all("auth.uid()" in sql for sql in policies)
    assert not any("FOR ALL" in sql or "FOR INSERT" in sql or "FOR UPDATE" in sql for sql in policies)
    assert not any("DISABLE ROW LEVEL SECURITY" in sql for sql in statements)
    assert any(
        "REVOKE EXECUTE ON FUNCTION public.rls_auto_enable()" in sql
        and "FROM PUBLIC, anon, authenticated" in sql
        for sql in statements
    )


def test_rls_migration_never_disables_access_protection_on_rollback(migration):
    with pytest.raises(RuntimeError, match="Security downgrade blocked"):
        migration.downgrade()
