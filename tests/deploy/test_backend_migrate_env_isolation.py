"""Backend migrations receive bounded settings without deployment secrets or database connections."""

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
COMPOSE = ROOT / "deploy/compose.game.yml"
SERVICE = "backend-migrate"
ALLOWLIST = {
    "DATABASE_URL",
    "GAME_DATABASE_URL",
    "MONGO_URL",
    "MONGO_DATABASE",
    "DEBUG",
    "DATABASE_ECHO",
    "MONGO_SERVER_SELECTION_TIMEOUT_MS",
    "LOG_LEVEL_CONSOLE",
    "LOG_LEVEL_FILE",
    "LOG_ROTATION",
    "LOG_DIR",
}
# Migrations depend on runtime infrastructure, not API authentication.
EXCLUDED = set(CANARIES) - {
    "DATABASE_URL",
    "GAME_DATABASE_URL",
    "MONGO_URL",
}


def test_backend_migrate_environment_is_an_explicit_allowlist():
    service = yaml.safe_load(COMPOSE.read_text())["services"][SERVICE]
    assert "env_file" not in service
    assert set(service["environment"]) == ALLOWLIST
    assert not EXCLUDED & service["environment"].keys()
    assert service["entrypoint"] == [
        "sh",
        "-c",
        "python src/backend/manage.py upgrade && python src/backend/manage.py ensure-mongo-indexes",
    ]


@pytest.mark.external
@pytest.mark.parametrize(
    "mode",
    [
        "defaults",
        "overrides",
        "empty",
        "site-key",
        "invalid-secrets",
        "invalid-service",
        "missing-auth",
        "empty-timeout",
        "empty-echo",
    ],
)
def test_backend_migrate_resolved_environment_and_offline_startup(tmp_path, mode):
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("Docker Compose CLI required; no containers are started")
    source = COMPOSE.read_text()
    names = set(re.findall(r"\$\{([A-Z][A-Z0-9_]*)", source))
    values = {key: "synthetic" for key in names if re.search(r"\$\{" + key + r":\?", source)}
    values.update(CANARIES)
    values.update(
        DOCKER_IMAGE_GAME="fake.invalid/game:test",
        DOCKER_IMAGE_CHAT="fake.invalid/chat:test",
        DOCKER_IMAGE_WORKER="fake.invalid/worker:test",
        GAME_DATABASE_URL="postgresql+asyncpg://synthetic:synthetic@db.invalid/game",  # pragma: allowlist secret
        SITE_DATABASE_URL="postgresql+asyncpg://synthetic:synthetic@db.invalid/site",  # pragma: allowlist secret
        REDIS_URL="redis://cache.invalid:6379/0",
        MONGO_URL="mongodb://mongo.invalid:27017",
        SECRET_KEY="synthetic-production-key",  # pragma: allowlist secret
        FRONTEND_INTERNAL_SERVICE_KEY="synthetic-service-key",  # pragma: allowlist secret
        DEBUG="True",
    )
    if mode == "overrides":
        values.update(
            DATABASE_ECHO="True",
            MONGO_SERVER_SELECTION_TIMEOUT_MS="1234",
            LOG_LEVEL_CONSOLE="WARNING",
            LOG_LEVEL_FILE="ERROR",
            LOG_ROTATION="20 MB",
            LOG_DIR="synthetic-logs",
            MONGO_DATABASE="synthetic_archive",
        )
    elif mode == "empty":
        values.update(LOG_LEVEL_CONSOLE="", LOG_LEVEL_FILE="", LOG_ROTATION="", LOG_DIR="")
    elif mode == "site-key":
        values.update(
            FRONTEND_INTERNAL_SERVICE_KEY="",
            SITE_TO_GAME_SERVICE_KEY="synthetic-fallback-key",  # pragma: allowlist secret - synthetic invalid fixture, never a real secret
        )  # pragma: allowlist secret
    elif mode == "invalid-secrets":
        values.update(SECRET_KEY="dev-rejected-key")  # pragma: allowlist secret
    elif mode == "invalid-service":
        values["FRONTEND_INTERNAL_SERVICE_KEY"] = "dev-rejected"  # pragma: allowlist secret - synthetic fixture
    elif mode == "empty-echo":
        values["DATABASE_ECHO"] = ""
    elif mode == "missing-auth":
        values.pop("FRONTEND_INTERNAL_SERVICE_KEY", None)
        values.pop("SITE_TO_GAME_SERVICE_KEY", None)
    elif mode == "empty-timeout":
        values["MONGO_SERVER_SELECTION_TIMEOUT_MS"] = ""
    fake_env = tmp_path / "synthetic.env"
    values["DEPLOY_ENV_FILE"] = fake_env.as_posix()
    fake_env.write_text("".join(f"{key}='{value}'\n" for key, value in values.items()))
    environment = os.environ.copy()
    for name in (
        names
        | set(CANARIES)
        | ALLOWLIST
        | {
            "PYTHONPATH",
            "COMPOSE_FILE",
            "COMPOSE_ENV_FILES",
            "COMPOSE_PROJECT_NAME",
        }
    ):
        environment.pop(name, None)
    result = subprocess.run(
        [docker, "compose", "--env-file", str(fake_env), "-f", str(COMPOSE), "config", "--format", "json"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, "Sanitized migration Compose config failed"
    service = json.loads(result.stdout)["services"][SERVICE]
    resolved = service["environment"]
    assert set(resolved) == ALLOWLIST
    assert not EXCLUDED & resolved.keys()
    assert not any(value in json.dumps(service) for key, value in CANARIES.items() if key in EXCLUDED)
    assert resolved["DEBUG"] == "False"
    assert resolved["DATABASE_URL"] == values["GAME_DATABASE_URL"]
    # Patch config construction before importing the actual module singleton. No .env
    # source exists in this process, and import constructs clients without connecting.
    script = """
import json
import pydantic_settings
original = pydantic_settings.SettingsConfigDict
def without_dotenv(*args, **kwargs):
    kwargs['env_file'] = None
    return original(*args, **kwargs)
pydantic_settings.SettingsConfigDict = without_dotenv
import socket
import io
import os
from pathlib import Path
def reject_connection(*args, **kwargs):
    raise AssertionError('Offline migration must not connect to a network')
socket.socket.connect = reject_connection
socket.create_connection = reject_connection
from src.backend.manage import run_migrations, ensure_mongo_indexes
from src.backend.config.runtime import runtime_settings as settings
from src.backend.core.database import async_engine
assert str(async_engine.url.database) == 'game'
from src.backend.infrastructure.mongo.client import get_mongo_provider
from src.backend.infrastructure.mongo.bootstrap import _default_repositories
provider = get_mongo_provider()
assert provider.url == settings.mongo_url
assert provider.database_name == settings.mongo_database
assert provider.server_selection_timeout_ms == settings.mongo_server_selection_timeout_ms
assert provider._client is None
# Build actual repository registrations over a local collection stub; no driver client.
class StubDatabase:
    def __getitem__(self, name):
        return object()
provider.database = lambda: StubDatabase()
assert len(_default_repositories()) == 6
from alembic import command
from alembic.config import Config
buffer = io.StringIO()
command.upgrade(Config(str(Path(os.environ['PYTHONPATH']) / 'src/backend/alembic.ini'), output_buffer=buffer), '0001_game_schema_baseline', sql=True)
sql = buffer.getvalue()
assert 'CREATE TABLE chat.' in sql
assert 'CREATE TABLE site.' not in sql
print(settings.model_dump_json())
"""
    # Clear every real settings field as well as aliases, using AST field names only.
    from tests.deploy._backend_environment import backend_environment_names

    fields = backend_environment_names(ROOT)
    for name in fields:
        environment.pop(name, None)
    parsed = subprocess.run(
        [sys.executable, "-c", script],
        env=dict(environment, PYTHONPATH=str(ROOT), **{k: v for k, v in resolved.items() if v is not None}),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if mode in {"empty-timeout", "empty-echo"}:
        assert parsed.returncode != 0
        assert ("mongo_server_selection_timeout_ms" if mode == "empty-timeout" else "database_echo") in parsed.stderr
        return
    assert parsed.returncode == 0, "Actual migration startup rejected sanitized resolved config: " + parsed.stderr
    settings = json.loads(parsed.stdout)
    assert settings["debug"] is False
    assert settings["database_url"] == settings["game_database_url"] == values["GAME_DATABASE_URL"]
    assert settings["mongo_url"] == values["MONGO_URL"]
    for key in ("log_level_console", "log_level_file", "log_rotation", "log_dir"):
        if mode in {"overrides", "empty"}:
            assert settings[key] == values[key.upper()]
    assert settings["database_echo"] is (mode == "overrides")
    assert settings["mongo_server_selection_timeout_ms"] == (1234 if mode == "overrides" else 5000)
    assert settings["mongo_database"] == ("synthetic_archive" if mode == "overrides" else "tbmmorpg_analytics")
    assert settings["gemini_api_key"] is None
    assert (
        not {
            "secret_key",
            "frontend_internal_service_key",
            "site_to_game_service_key",
            "asset_s3_secret_access_key",
            "operator_write_key",
        }
        & settings.keys()
    )
