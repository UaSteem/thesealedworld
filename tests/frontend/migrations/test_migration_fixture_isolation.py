"""Safety contracts for disposable migration/auth PostgreSQL helpers; never connect."""

import os
import subprocess
import sys

import pytest
from tests.frontend.migrations import test_site_migrations_postgres as fixture

DISPOSABLE = "postgresql://postgres@127.0.0.1:25432/site_migration_012345abcdef"
EXPECTED = DISPOSABLE.replace("postgresql://", "postgresql+asyncpg://")
CAPTURE = """
import sqlalchemy.ext.asyncio as sa

def capture(url, **kwargs):
    print('CAPTURE=' + str(url))
    raise RuntimeError('capture-only; connection forbidden')
sa.create_async_engine = capture
"""


def run(script, tmp_path, *, capture=CAPTURE):
    # Deliberately hostile inherited DB values; fixture bootstrap must eliminate them.
    env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "COMSPEC", "PATHEXT"}
    }
    env.update(
        PYTHONPATH=str(fixture.ROOT),
        DATABASE_URL="postgresql+asyncpg://postgres@ambient.invalid/working",
        SITE_DATABASE_URL="postgresql+asyncpg://postgres@ambient.invalid/working",
        PGHOST="ambient.invalid",
        PGDATABASE="working",
        PGSERVICE="ambient",
        DEBUG="True",
    )
    return subprocess.run(
        [sys.executable, "-c", capture + fixture.BOOTSTRAP + script, DISPOSABLE],
        cwd=fixture.ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_bootstrap_routes_actual_database_module_to_disposable_before_engine(tmp_path):
    result = run("\nfrom src.frontend.core.database import Base", tmp_path)
    assert "CAPTURE=" + EXPECTED in result.stdout
    assert "ambient.invalid" not in result.stdout
    assert "capture-only" in result.stderr


@pytest.mark.parametrize(
    "call",
    [
        "sa.create_async_engine('postgresql+asyncpg://postgres@ambient.invalid/working')",
        "sa.async_engine_from_config({'sqlalchemy.url': 'postgresql+asyncpg://postgres@ambient.invalid/working'})",
    ],
)
def test_misrouted_engine_url_is_rejected_before_factory(tmp_path, call):
    result = run("\n" + call, tmp_path)
    assert result.returncode != 0
    assert "outside disposable PostgreSQL fixture" in result.stderr
    assert "CAPTURE=" not in result.stdout


@pytest.mark.parametrize(
    "url",
    [
        "postgresql://postgres@127.0.0.1:5432/site",
        "postgresql://postgres@ambient.invalid:25432/site_migration_012345abcdef",
        "postgresql://postgres@127.0.0.1:25432/working",
    ],
)
def test_helper_rejects_non_disposable_database_before_subprocess(url, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Subprocess must not start")

    monkeypatch.setattr(fixture.subprocess, "run", forbidden)
    with pytest.raises(ValueError, match="disposable"):
        fixture.migrate(url)


def test_fixture_subprocess_environment_excludes_all_application_and_pg_inputs(monkeypatch):
    for name in [
        "DATABASE_URL",
        "SITE_DATABASE_URL",
        "PGHOST",
        "PGDATABASE",
        "PGPASSWORD",
        "PGSERVICE",
        "PGSERVICEFILE",
        "PGOPTIONS",
    ]:
        monkeypatch.setenv(name, "ambient-value")
    environment = fixture._subprocess_env()
    assert not any(key.startswith("PG") or key.endswith("DATABASE_URL") for key in environment)


def test_valid_shape_but_unregistered_url_is_rejected():
    with pytest.raises(ValueError, match="not registered"):
        fixture._disposable_url(DISPOSABLE)


def test_actual_alembic_online_factory_receives_only_disposable_url(tmp_path):
    prefix = """
import sqlalchemy.ext.asyncio as sa
from types import SimpleNamespace
sa.create_async_engine = lambda *args, **kwargs: SimpleNamespace()
def capture_config(configuration, prefix='sqlalchemy.', **kwargs):
    print('CAPTURE=' + str(configuration[prefix + 'url']))
    raise RuntimeError('capture-only; connection forbidden')
sa.async_engine_from_config = capture_config
"""
    result = run("\ncommand.upgrade(config, 'head')", tmp_path, capture=prefix)
    assert "CAPTURE=" + EXPECTED in result.stdout
    assert "ambient.invalid" not in result.stdout
    assert "capture-only" in result.stderr
