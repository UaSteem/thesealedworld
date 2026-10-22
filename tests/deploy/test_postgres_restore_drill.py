"""Opt-in synthetic backup/restore drill; never connects to application databases."""

import os
import subprocess
import time
from uuid import uuid4

import pytest

pytestmark = [
    pytest.mark.external,
    pytest.mark.skipif(os.getenv("RUN_POSTGRES_RESTORE_DRILL") != "1", reason="Opt-in disposable PostgreSQL drill"),
]


def test_postgres_custom_archives_restore_data_constraints_and_sequences():
    container = f"tbmm-restore-drill-{uuid4().hex}"

    def docker(*args: str, input_text: str | None = None, check: bool = True):
        return subprocess.run(
            ["docker", *args],
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=check,
        )

    def sql(database: str, statement: str):
        return docker(
            "exec",
            "-i",
            container,
            "psql",
            "-X",
            "-U",
            "postgres",
            "-d",
            database,
            "-v",
            "ON_ERROR_STOP=1",
            "-At",
            input_text=statement,
        ).stdout.strip()

    try:
        docker(
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
        for _ in range(60):
            ready = docker("exec", container, "pg_isready", "-U", "postgres", check=False)
            if ready.returncode == 0:
                break
            time.sleep(0.5)
        else:
            pytest.fail("Disposable PostgreSQL did not become ready")

        for domain, table, text in (("site", "members", "почта ✓"), ("game", "objects", "предмет 雪")):
            source, restored = f"drill_{domain}_source", f"drill_{domain}_restored"
            for database in (source, restored):
                docker("exec", container, "createdb", "-U", "postgres", "-T", "template0", "--encoding=UTF8", database)
            sql(
                source,
                f"""
                CREATE TABLE {table} (
                    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    code text NOT NULL UNIQUE,
                    label text NOT NULL,
                    amount integer NOT NULL CHECK (amount > 0)
                );
                CREATE INDEX {table}_label_idx ON {table}(label);
                INSERT INTO {table}(code,label,amount) VALUES ('{domain}', '{text}', 7), ('deleted', 'old', 1);
                DELETE FROM {table} WHERE code='deleted';
            """,
            )
            archive = f"/tmp/{domain}.dump"
            docker("exec", container, "pg_dump", "-U", "postgres", "--format=custom", "--file", archive, source)
            docker(
                "exec",
                container,
                "pg_restore",
                "-U",
                "postgres",
                "--exit-on-error",
                "--single-transaction",
                "--dbname",
                restored,
                archive,
            )
            assert (
                sql(restored, f"SELECT id || '|' || code || '|' || label || '|' || amount FROM {table}")
                == f"1|{domain}|{text}|7"
            )
            assert sql(restored, "SELECT tablename FROM pg_tables WHERE schemaname='public'") == table
            assert sql(restored, f"SELECT count(*) FROM pg_indexes WHERE tablename='{table}'") == "3"
            assert (
                sql(restored, f"INSERT INTO {table}(code,label,amount) VALUES ('new','next',1) RETURNING id")
                == "3\nINSERT 0 1"
            )
            for values in (f"('{domain}','duplicate',1)", "('bad','invalid',0)", "('null',NULL,1)"):
                rejected = docker(
                    "exec",
                    "-i",
                    container,
                    "psql",
                    "-X",
                    "-U",
                    "postgres",
                    "-d",
                    restored,
                    "-v",
                    "ON_ERROR_STOP=1",
                    input_text=f"INSERT INTO {table}(code,label,amount) VALUES {values};",
                    check=False,
                )
                assert rejected.returncode != 0, "Restored database must enforce original constraints"
            assert sql(source, f"SELECT count(*) FROM {table}") == "1"

        docker("exec", container, "createdb", "-U", "postgres", "drill_corrupt_target")
        docker(
            "exec",
            "-i",
            container,
            "sh",
            "-c",
            "cat > /tmp/corrupt.dump",
            input_text="PGDMP deliberately corrupt archive",
        )
        failed = docker(
            "exec",
            container,
            "pg_restore",
            "-U",
            "postgres",
            "--exit-on-error",
            "--single-transaction",
            "--dbname",
            "drill_corrupt_target",
            "/tmp/corrupt.dump",
            check=False,
        )
        assert failed.returncode != 0, "Corrupted archive must not be reported as restored"
        assert sql("drill_corrupt_target", "SELECT count(*) FROM pg_tables WHERE schemaname='public'") == "0"
    finally:
        docker("rm", "--force", "--volumes", container, check=False)
        remaining = docker("ps", "--all", "--quiet", "--filter", f"name=^/{container}$")
        assert not remaining.stdout.strip(), "Disposable drill container cleanup failed"
