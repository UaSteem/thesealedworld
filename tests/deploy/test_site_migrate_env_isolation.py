"""Site migrations receive only explicit settings; all credentials below are synthetic."""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from tests.deploy.test_bot_env_isolation import CANARIES

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy/compose.site.yml"
SERVICE = "site-migrate"
ALLOWLIST = {
    "DATABASE_URL",
    "SITE_DATABASE_URL",
    "DEBUG",
    "DATABASE_ECHO",
    "LOG_LEVEL_CONSOLE",
    "LOG_LEVEL_FILE",
    "LOG_ROTATION",
    "LOG_DIR",
}
EXCLUDED = set(CANARIES) - {"DATABASE_URL", "SITE_DATABASE_URL"}


def test_site_migrate_has_explicit_environment():
    service = yaml.safe_load(COMPOSE.read_text())["services"][SERVICE]
    assert "env_file" not in service
    assert set(service["environment"]) == ALLOWLIST
    assert not EXCLUDED & service["environment"].keys()
    assert service["entrypoint"] == ["alembic", "-c", "src/frontend/alembic.ini", "upgrade", "head"]


@pytest.mark.external
@pytest.mark.parametrize(
    "mode", ["defaults", "overrides", "empty", "missing-auth", "invalid-secret", "invalid-service", "empty-echo"]
)
def test_resolved_site_migrate_settings_and_offline_sql(tmp_path, mode):
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("Docker Compose CLI required; no containers are started")
    source = COMPOSE.read_text()
    names = set(re.findall(r"\$\{([A-Z][A-Z0-9_]*)", source))
    values = {key: "synthetic" for key in names if re.search(r"\$\{" + key + r":\?", source)}
    values.update(CANARIES)
    values.update(
        DOCKER_IMAGE_SITE="fake.invalid/site:test",
        SITE_DATABASE_URL="postgresql+asyncpg://synthetic:synthetic@db.invalid/site",  # pragma: allowlist secret - synthetic fixture
        SECRET_KEY="synthetic-production-key",  # pragma: allowlist secret - synthetic fixture
        BACKEND_INTERNAL_SERVICE_KEY="synthetic-service-key",  # pragma: allowlist secret - synthetic fixture
        DEBUG="True",
    )
    if mode == "overrides":
        values.update(
            DATABASE_ECHO="True",
            LOG_LEVEL_CONSOLE="WARNING",
            LOG_LEVEL_FILE="ERROR",
            LOG_ROTATION="20 MB",
            LOG_DIR="synthetic-logs",
        )
    elif mode == "empty":
        values.update(LOG_LEVEL_CONSOLE="", LOG_LEVEL_FILE="", LOG_ROTATION="", LOG_DIR="")
    elif mode == "missing-auth":
        pass  # Other services still require it; the migration allowlist excludes it.
    elif mode == "invalid-secret":
        values["SECRET_KEY"] = "dev-rejected"  # pragma: allowlist secret - synthetic fixture
    elif mode == "invalid-service":
        values["BACKEND_INTERNAL_SERVICE_KEY"] = "dev-rejected"  # pragma: allowlist secret - synthetic fixture
    elif mode == "empty-echo":
        values["DATABASE_ECHO"] = ""
    fake_env = tmp_path / "synthetic.env"
    values["DEPLOY_ENV_FILE"] = fake_env.as_posix()
    fake_env.write_text("".join(f"{key}='{value}'\n" for key, value in values.items()))
    fields = set()
    for source in (ROOT / "src/frontend/config").glob("*.py"):
        tree = ast.parse(source.read_text())
        fields.update(
            node.target.id.upper()
            for node in ast.walk(tree)
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        )
    environment = os.environ.copy()
    for name in (
        names
        | set(CANARIES)
        | ALLOWLIST
        | fields
        | {"PYTHONPATH", "COMPOSE_FILE", "COMPOSE_ENV_FILES", "COMPOSE_PROJECT_NAME"}
    ):
        environment.pop(name, None)
    result = subprocess.run(
        [docker, "compose", "--env-file", str(fake_env), "-f", str(COMPOSE), "config", "--format", "json"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, "Sanitized site Compose config failed"
    service = json.loads(result.stdout)["services"][SERVICE]
    resolved = service["environment"]
    assert set(resolved) == ALLOWLIST
    assert not EXCLUDED & resolved.keys()
    assert not any(value in json.dumps(service) for key, value in CANARIES.items() if key in EXCLUDED)
    assert resolved["DATABASE_URL"] == resolved["SITE_DATABASE_URL"] == values["SITE_DATABASE_URL"]
    assert resolved["DEBUG"] == "False"
    script = r"""
import io
import json
import socket
import pydantic_settings
original = pydantic_settings.SettingsConfigDict
def without_dotenv(*args, **kwargs):
    kwargs['env_file'] = None
    return original(*args, **kwargs)
pydantic_settings.SettingsConfigDict = without_dotenv
def reject_connection(*args, **kwargs):
    raise AssertionError('Offline migration must not connect to a network')
socket.socket.connect = reject_connection
socket.create_connection = reject_connection
from src.frontend.config.database import database_settings as settings
from src.frontend.core.database import async_engine
assert str(async_engine.url.database) == 'site'
from alembic import command
from alembic.config import Config
from pathlib import Path
buffer = io.StringIO()
command.upgrade(Config(str(Path(__import__('os').environ['PYTHONPATH']) / 'src/frontend/alembic.ini'), output_buffer=buffer), '0001_site_schema_baseline', sql=True)
sql = buffer.getvalue()
assert 'CREATE TABLE site.auth_users' in sql
assert 'CREATE TABLE site.articles' in sql
assert 'CREATE TABLE game.' not in sql
print(settings.model_dump_json())
"""
    parsed = subprocess.run(
        [sys.executable, "-c", script],
        env=dict(
            environment, PYTHONPATH=str(ROOT), **{key: value for key, value in resolved.items() if value is not None}
        ),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if mode == "empty-echo":
        assert parsed.returncode != 0
        assert "database_echo" in parsed.stderr
        return
    assert parsed.returncode == 0, parsed.stderr
    settings = json.loads(parsed.stdout)
    assert settings["debug"] is False
    assert settings["database_url"] == settings["site_database_url"] == values["SITE_DATABASE_URL"]
    assert settings["database_echo"] is (mode == "overrides")
    for key in ("log_level_console", "log_level_file", "log_rotation", "log_dir"):
        if mode in {"overrides", "empty"}:
            assert settings[key] == values[key.upper()]
    assert (
        not {
            "secret_key",
            "backend_internal_service_key",
            "smtp_password",
            "asset_s3_secret_access_key",
            "backend_operator_write_key",
        }
        & settings.keys()
    )
