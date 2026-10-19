"""Opt-in real PostgreSQL proof; creates and destroys only its own Docker container.

Run with RUN_SITE_MIGRATION_POSTGRES=1; no real database URL or .env is read.
"""

import asyncio
import hashlib
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import asyncpg
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_SITE_MIGRATION_POSTGRES") != "1", reason="explicit disposable PostgreSQL opt-in required"
)
ROOT = Path(__file__).resolve().parents[3]
BASELINE = "0001_site_schema_baseline"
HEAD = ScriptDirectory.from_config(Config(str(ROOT / "src/frontend/alembic.ini"))).get_current_head()
USER_ID = "77ed3260-511e-45ec-967f-dd5290123248"


def docker(*args):
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture(scope="module")
def postgres():
    name = "tbmmorpg-site-migrations-" + uuid.uuid4().hex[:12]
    docker("image", "inspect", "postgres:16-alpine")
    docker(
        "run",
        "--detach",
        "--rm",
        "--name",
        name,
        "--publish",
        "127.0.0.1::5432",
        "--env",
        "POSTGRES_HOST_AUTH_METHOD=trust",
        "postgres:16-alpine",
    )
    try:
        for _ in range(60):
            result = subprocess.run(["docker", "exec", name, "pg_isready", "-U", "postgres"], capture_output=True)
            if result.returncode == 0:
                break
            time.sleep(0.5)
        else:
            pytest.fail("Disposable PostgreSQL did not become ready")
        mapping = docker("port", name, "5432/tcp")
        assert mapping.startswith("127.0.0.1:")
        yield name, int(mapping.rsplit(":", 1)[1])
    finally:
        docker("rm", "--force", name)


@pytest.fixture
def database(postgres):
    name, port = postgres
    db = "site_migration_" + uuid.uuid4().hex[:12]
    docker("exec", name, "createdb", "-U", "postgres", db)
    return f"postgresql://postgres@127.0.0.1:{port}/{db}"


def sql(url, query, *args):
    async def run():
        connection = await asyncpg.connect(url)
        try:
            return [dict(row) for row in await connection.fetch(query, *args)]
        finally:
            await connection.close()

    return asyncio.run(run())


BOOTSTRAP = r"""
import sys, types
from types import SimpleNamespace
from alembic.config import Config
from alembic import command
module = types.ModuleType('src.frontend.config.settings')
module.settings = SimpleNamespace(database_url=sys.argv[1].replace('postgresql://', 'postgresql+asyncpg://'), database_echo=False)
sys.modules['src.frontend.config.settings'] = module
config = Config('src/frontend/alembic.ini')
"""


def migrate(url, direction="upgrade", revision="head", *, check=True):
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            BOOTSTRAP + "\ngetattr(command, sys.argv[2])(config, sys.argv[3])",
            url,
            direction,
            revision,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if check:
        assert result.returncode == 0, result.stderr
    return result


def schema_diff(url):
    script = (
        BOOTSTRAP
        + r"""
import asyncio
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy.ext.asyncio import create_async_engine
from src.frontend.core.database import Base, model_imports
async def check():
    engine = create_async_engine(module.settings.database_url)
    def compare(connection):
        context = MigrationContext.configure(connection, opts={
            'include_schemas': True, 'compare_type': True, 'compare_server_default': True,
            'include_object': lambda obj, name, kind, reflected, compare_to: name != 'alembic_version',
        })
        differences = compare_metadata(context, Base.metadata)
        assert not differences, repr(differences)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(compare)
    finally:
        await engine.dispose()
asyncio.run(check())
"""
    )
    result = subprocess.run([sys.executable, "-c", script, url], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_clean_upgrade_repeated_upgrade_and_head_matches_current_metadata(database):
    migrate(database)
    assert sql(database, "SELECT version_num FROM alembic_version") == [{"version_num": HEAD}]
    migrate(database)
    schema_diff(database)


def test_upgrade_populated_historical_baseline_preserves_data(database):
    migrate(database, revision=BASELINE)
    sql(
        database,
        "INSERT INTO site.auth_users (id,email,hashed_password,is_active,is_superuser,tester_status) VALUES ($1,'migration@example.test','synthetic-hash',true,false,'none')",
        uuid.UUID(USER_ID),
    )
    sql(
        database,
        "INSERT INTO site.auth_refresh_tokens (user_id,token,expires_at) VALUES ($1,'synthetic-refresh',now()+interval '1 day')",
        uuid.UUID(USER_ID),
    )
    sql(
        database,
        "INSERT INTO site.articles (slug,title,preview,body,is_published) VALUES ('migration','Original','Preview','Body',false)",
    )
    survey_id = sql(database, "INSERT INTO site.surveys (title) VALUES ('Baseline survey') RETURNING id")[0]["id"]
    sql(
        database,
        "INSERT INTO site.survey_questions (survey_id,text,question_type,\"order\") VALUES ($1,'Question','text',0)",
        survey_id,
    )
    send_id = sql(
        database,
        "INSERT INTO site.survey_sends (survey_id,user_id,token) VALUES ($1,$2,'synthetic-survey-token') RETURNING id",
        survey_id,
        uuid.UUID(USER_ID),
    )[0]["id"]
    sql(database, "INSERT INTO site.survey_responses (send_id,answers_json) VALUES ($1,'{}')", send_id)
    sql(
        database,
        "INSERT INTO site.feedback (user_id,type,title,body,status) VALUES ($1,'bug','Original feedback','Body','new')",
        uuid.UUID(USER_ID),
    )
    sql(
        database,
        "INSERT INTO site.player_daily_activity (player_id,date,first_seen,last_seen) VALUES ($1,current_date,now(),now())",
        uuid.UUID(USER_ID),
    )
    migrate(database)
    assert (
        sql(database, "SELECT email,referral_code,email_verified_at FROM site.auth_users")[0]["email"]
        == "migration@example.test"
    )
    code = sql(database, "SELECT referral_code FROM site.auth_users")[0]["referral_code"]
    assert code.startswith("SEAL-") and len(code) == 13
    assert sql(database, "SELECT token_hash FROM site.auth_refresh_tokens") == [
        {"token_hash": hashlib.sha256(b"synthetic-refresh").hexdigest()}
    ]
    assert sql(database, "SELECT title FROM site.articles") == [{"title": "Original"}]
    for table in (
        "surveys",
        "survey_questions",
        "survey_sends",
        "survey_responses",
        "feedback",
        "player_daily_activity",
    ):
        assert sql(database, f"SELECT count(*) AS count FROM site.{table}") == [{"count": 1}]
    migrate(database)
    assert sql(database, "SELECT referral_code FROM site.auth_users")[0]["referral_code"] == code


def test_baseline_downgrade_refuses_to_cascade_foreign_objects(database):
    migrate(database, revision=BASELINE)
    sql(database, "CREATE TABLE site.foreign_owner_table (id integer PRIMARY KEY)")
    sql(database, "INSERT INTO site.foreign_owner_table VALUES (7)")
    result = migrate(database, "downgrade", "base", check=False)
    assert result.returncode != 0
    assert sql(database, "SELECT id FROM site.foreign_owner_table") == [{"id": 7}]
    assert sql(database, "SELECT version_num FROM alembic_version") == [{"version_num": BASELINE}]
    assert sql(database, "SELECT to_regclass('site.auth_users') AS name") == [{"name": "site.auth_users"}]


def test_rollback_and_reapply_preserves_baseline_data(database):
    migrate(database, revision=BASELINE)
    sql(
        database,
        "INSERT INTO site.auth_users (id,email,hashed_password,is_active,is_superuser,tester_status) VALUES ($1,'rollback@example.test','synthetic-hash',true,false,'none')",
        uuid.UUID(USER_ID),
    )
    sql(
        database,
        "INSERT INTO site.auth_refresh_tokens (user_id,token,expires_at) VALUES ($1,'synthetic-rollback-refresh',now()+interval '1 day')",
        uuid.UUID(USER_ID),
    )
    migrate(database)
    assert len(sql(database, "SELECT token_hash FROM site.auth_refresh_tokens")) == 1
    migrate(database, "downgrade", BASELINE)
    assert sql(database, "SELECT email FROM site.auth_users") == [{"email": "rollback@example.test"}]
    assert sql(database, "SELECT token FROM site.auth_refresh_tokens") == [{"token": None}]
    # Raw refresh secrets cannot be recovered from SHA-256 hashes on downgrade.
    # Re-upgrade discards rows whose restored token is NULL (0002 contract).
    migrate(database)
    assert sql(database, "SELECT token_hash FROM site.auth_refresh_tokens") == []
    schema_diff(database)
    migrate(database, "downgrade", "base")
    assert sql(database, "SELECT schema_name FROM information_schema.schemata WHERE schema_name='site'") == []


@pytest.mark.parametrize("canonical", [False, True])
def test_populated_0004_index_upgrade_and_rollback(database, canonical):
    migrate(database, revision="0004_email_verification")
    sql(
        database,
        "INSERT INTO site.auth_users (id,email,hashed_password,is_active,is_superuser,tester_status,referral_code) VALUES ($1,'indexes@example.test','synthetic-hash',true,false,'none','SEAL-ABCDEFGH')",
        uuid.UUID(USER_ID),
    )
    sql(
        database,
        "INSERT INTO site.auth_refresh_tokens (user_id,token_hash,expires_at) VALUES ($1,$2,now()+interval '1 day')",
        uuid.UUID(USER_ID),
        hashlib.sha256(b"synthetic-refresh").hexdigest(),
    )
    names = [
        ("auth_refresh_tokens", "token_hash"),
        ("auth_users", "referral_code"),
        ("auth_users", "referred_by_id"),
        ("auth_email_verification_tokens", "token_hash"),
    ]
    if canonical:
        for table, column in names:
            sql(database, f'ALTER INDEX site."ix_{table}_{column}" RENAME TO "ix_site_{table}_{column}"')
    before = sql(database, "SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='site'")
    migrate(database)
    schema_diff(database)
    assert sql(database, "SELECT email,referral_code FROM site.auth_users") == [
        {"email": "indexes@example.test", "referral_code": "SEAL-ABCDEFGH"}
    ]
    assert len(sql(database, "SELECT token_hash FROM site.auth_refresh_tokens")) == 1
    assert len(sql(database, "SELECT indexname FROM pg_indexes WHERE schemaname='site'")) == len(before)
    migrate(database, "downgrade", "0004_email_verification")
    actual = {row["indexname"] for row in sql(database, "SELECT indexname FROM pg_indexes WHERE schemaname='site'")}
    assert all(f"ix_{table}_{column}" in actual for table, column in names)
    assert sql(database, "SELECT referral_code FROM site.auth_users") == [{"referral_code": "SEAL-ABCDEFGH"}]


@pytest.mark.parametrize("conflict", ["wrong_definition", "duplicate_names"])
def test_index_conflicts_fail_transactionally_without_reconciling_unknown_schema(database, conflict):
    migrate(database, revision="0004_email_verification")
    column = "email" if conflict == "wrong_definition" else "referral_code"
    sql(database, f"CREATE UNIQUE INDEX ix_site_auth_users_referral_code ON site.auth_users ({column})")
    before = sql(database, "SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='site' ORDER BY indexname")
    result = migrate(database, check=False)
    assert result.returncode != 0
    assert "reconcile manually" in result.stderr
    assert sql(database, "SELECT version_num FROM alembic_version") == [{"version_num": "0004_email_verification"}]
    assert (
        sql(database, "SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='site' ORDER BY indexname") == before
    )


def test_baseline_is_independent_of_future_application_metadata(database):
    script = (
        BOOTSTRAP
        + """
import sqlalchemy as sa
from src.frontend.core.database import Base, model_imports
Base.metadata.tables['site.auth_users'].append_column(sa.Column('future_field', sa.String()))
sa.Table('future_feature', Base.metadata, sa.Column('id', sa.Integer(), primary_key=True))
command.upgrade(config, '0001_site_schema_baseline')
"""
    )
    result = subprocess.run([sys.executable, "-c", script, database], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert sql(database, "SELECT to_regclass('site.future_feature') AS name") == [{"name": None}]
    columns = {
        row["column_name"]
        for row in sql(
            database,
            "SELECT column_name FROM information_schema.columns WHERE table_schema='site' AND table_name='auth_users'",
        )
    }
    assert not columns.intersection({"future_field", "referral_code", "referred_by_id", "email_verified_at"})
    assert sql(
        database,
        "SELECT column_name FROM information_schema.columns WHERE table_schema='site' AND table_name='auth_refresh_tokens' AND column_name IN ('token','token_hash')",
    ) == [{"column_name": "token"}]
