"""Disposable PostgreSQL semantics; never connects to selected/application sources."""

import os
import subprocess
import time
from uuid import uuid4

import pytest

pytestmark = [
    pytest.mark.external,
    pytest.mark.skipif(
        os.getenv("RUN_STUDIO_POSTGRES_READONLY_DRILL") != "1", reason="Opt-in disposable Studio read-only drill"
    ),
]


def test_postgres_readonly_rejects_cte_and_mutating_function():
    container = "tbmm-studio-ro-" + uuid4().hex

    def docker(*args, input_text=None):
        return subprocess.run(["docker", *args], input=input_text, capture_output=True, text=True, timeout=30)

    def sql(statement):
        return docker(
            "exec",
            "-i",
            container,
            "psql",
            "-X",
            "-U",
            "postgres",
            "-v",
            "ON_ERROR_STOP=1",
            "-At",
            input_text=statement,
        )

    try:
        started = docker(
            "run",
            "--detach",
            "--pull=never",
            "--name",
            container,
            "--network=none",
            "--tmpfs",
            "/var/lib/postgresql/data:rw",
            "-e",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            "postgres:16-alpine",
        )
        assert started.returncode == 0, "Disposable PostgreSQL could not start"
        for _ in range(60):
            if docker("exec", container, "pg_isready", "-U", "postgres").returncode == 0:
                break
            time.sleep(0.25)
        else:
            pytest.fail("Disposable PostgreSQL not ready")
        created = sql(
            "CREATE TABLE evidence (id integer); CREATE FUNCTION mutate() RETURNS integer LANGUAGE plpgsql AS $$ BEGIN INSERT INTO evidence VALUES (1); RETURN 1; END $$;"
        )
        assert created.returncode == 0
        for query in [
            "WITH written AS (INSERT INTO evidence VALUES (2) RETURNING id) SELECT * FROM written;",
            "SELECT mutate();",
        ]:
            failed = sql("SET default_transaction_read_only=on; BEGIN READ ONLY; " + query)
            assert failed.returncode != 0
            assert "read-only transaction" in failed.stderr
        assert sql("SELECT count(*) FROM evidence;").stdout.strip() == "0"
    finally:
        cleaned = docker("rm", "--force", "--volumes", container)
        assert cleaned.returncode == 0, "Disposable Studio container cleanup failed"
