"""Opt-in disposable MongoDB contract; never connects to project services."""

import os
import subprocess
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMAGE = "mongo:8@sha256:0e900a3364da37b76d642b73b0bba56bd4c6c509ab470cf700436fd866bee3ff"
SCRIPT = ROOT / "deploy/mongo/provision-runtime-user.js"


@pytest.mark.external
def test_provisioned_mongo_user_is_database_scoped():
    if os.environ.get("RUN_MONGO_PROVISIONING_CONTRACT") != "1":
        pytest.skip("Opt in to a disposable Mongo container with RUN_MONGO_PROVISIONING_CONTRACT=1")
    name = "tbmmorpg-provision-test-" + uuid.uuid4().hex[:12]

    def docker(*args, check=True):
        result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=90)
        if check:
            assert result.returncode == 0, result.stderr
        return result

    def shell(script, *, runtime=False, provisioning=False, check=True):
        args = ["exec"]
        if provisioning:
            for key, value in {
                "MONGO_PROVISION_CONFIRM": "create-database-user",
                "MONGO_PROVISION_DATABASE": "isolated_app",
                "MONGO_PROVISION_USERNAME": "application",
                "MONGO_PROVISION_PASSWORD": "synthetic-application-password-12345",  # pragma: allowlist secret - disposable test fixture
            }.items():
                args.extend(["-e", f"{key}={value}"])
        args.extend(
            [
                name,
                "mongosh",
                "--quiet",
                "--host",
                "127.0.0.1",
                "-u",
                "application" if runtime else "synthetic_admin",
                "-p",
                "synthetic-application-password-12345" if runtime else "synthetic-admin-password-12345",
                "--authenticationDatabase",
                "isolated_app" if runtime else "admin",
            ]
        )
        args.extend(["--file", "/tmp/provision.js"] if script is None else ["--eval", script])
        return docker(*args, check=check)

    try:
        docker(
            "run",
            "-d",
            "--name",
            name,
            "--network",
            "none",
            "-e",
            "MONGO_INITDB_ROOT_USERNAME=synthetic_admin",  # pragma: allowlist secret - disposable test fixture
            "-e",
            "MONGO_INITDB_ROOT_PASSWORD=synthetic-admin-password-12345",  # pragma: allowlist secret - disposable test fixture
            IMAGE,
        )
        # The official image starts a temporary initialization daemon before the
        # final process. Wait inside the container for both init and auth readiness.
        docker(
            "exec",
            name,
            "sh",
            "-c",
            "for i in $(seq 1 60); do "
            "mongosh --quiet -u synthetic_admin -p synthetic-admin-password-12345 "
            "--authenticationDatabase admin --eval 'db.adminCommand({ping:1})' >/dev/null 2>&1 "
            '&& test "$(cat /proc/1/comm)" = mongod && exit 0; sleep 1; done; exit 1',
        )
        docker("cp", str(SCRIPT), name + ":/tmp/provision.js")
        assert shell(None, check=False).returncode != 0  # no explicit confirmation
        shell(None, provisioning=True)
        assert shell(None, provisioning=True, check=False).returncode != 0  # no silent rotation
        shell(
            "const d=db.getSiblingDB('isolated_app'); d.probe.insertOne({value:1}); "
            "d.probe.createIndex({value:1}); if(d.probe.countDocuments({})!==1) throw Error('Insert/read failed');",
            runtime=True,
        )
        shell(
            "let denied=false; try { db.getSiblingDB('other_app').probe.insertOne({x:1}); } "
            "catch(e) { denied=e.code===13; } if(!denied) throw Error('Cross-database write allowed'); "
            "let adminDenied=false; try { db.getSiblingDB('admin').runCommand({usersInfo:1}); } "
            "catch(e) { adminDenied=e.code===13; } if(!adminDenied) throw Error('Admin operation allowed');",
            runtime=True,
        )
    finally:
        docker("rm", "-f", name, check=False)
