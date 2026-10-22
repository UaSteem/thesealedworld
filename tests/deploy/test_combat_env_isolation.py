"""Combat worker receives a bounded environment without reading deployment secrets."""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from tests.deploy.test_bot_env_isolation import CANARIES as BOT_CANARIES

CANARIES = dict(BOT_CANARIES, OPENROUTER_API_KEY="canary-openrouter")  # pragma: allowlist secret

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy/compose.game.yml"
SERVICE = "combat-worker"
ALLOWLIST = {
    "DATABASE_URL",
    "GAME_DATABASE_URL",
    "REDIS_URL",
    "MONGO_URL",
    "MONGO_DATABASE",
    "DEBUG",
    "DATABASE_ECHO",
    "MONGO_SERVER_SELECTION_TIMEOUT_MS",
    "LOG_LEVEL_CONSOLE",
    "LOG_LEVEL_FILE",
    "LOG_ROTATION",
    "LOG_DIR",
    "GAME_STREAM_NAME",
    "GAME_STREAM_MAXLEN",
    "COMBAT_AI_POLICY_PATH",
    "DEFAULT_SYMBIOTE_NAME",
    "GAME_REFRESH_TOKEN_EXPIRE_MINUTES",
}
# Combat runtime workers do not consume API credentials.
EXCLUDED = set(CANARIES) - {
    "DATABASE_URL",
    "GAME_DATABASE_URL",
    "MONGO_URL",
}


def test_combat_environment_is_an_explicit_allowlist():
    service = yaml.safe_load(COMPOSE.read_text())["services"][SERVICE]
    assert "env_file" not in service
    assert set(service["environment"]) == ALLOWLIST
    assert not EXCLUDED & service["environment"].keys()
    assert service["command"] == ["arq", "src.backend.features.combat.workers.arq.CombatArqSettings"]


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
        "empty-stream-maxlen",
        "empty-refresh-ttl",
    ],
)
def test_combat_resolved_environment_and_actual_worker_import(tmp_path, mode):
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
            MONGO_DATABASE="synthetic_combat",
            DEFAULT_SYMBIOTE_NAME="synthetic-symbiote",
            GAME_REFRESH_TOKEN_EXPIRE_MINUTES="123",
            GAME_STREAM_NAME="synthetic_events",
            GAME_STREAM_MAXLEN="456",
            COMBAT_AI_POLICY_PATH="synthetic-policy.json",
        )
    elif mode == "empty":
        values.update(DEFAULT_SYMBIOTE_NAME="", GAME_STREAM_NAME="", COMBAT_AI_POLICY_PATH="")
        values.update(LOG_LEVEL_CONSOLE="", LOG_LEVEL_FILE="", LOG_ROTATION="", LOG_DIR="")
    elif mode == "site-key":
        values.update(
            FRONTEND_INTERNAL_SERVICE_KEY="",
            SITE_TO_GAME_SERVICE_KEY="synthetic-fallback-key",  # pragma: allowlist secret - synthetic invalid fixture, never a real secret
        )  # pragma: allowlist secret
    elif mode == "invalid-secrets":
        values.update(SECRET_KEY="dev-rejected-key")  # pragma: allowlist secret
    elif mode == "missing-auth":
        values.pop("FRONTEND_INTERNAL_SERVICE_KEY", None)
        values.pop("SITE_TO_GAME_SERVICE_KEY", None)
    elif mode == "invalid-service":
        values["FRONTEND_INTERNAL_SERVICE_KEY"] = "dev-rejected"  # pragma: allowlist secret
    elif mode == "empty-echo":
        values["DATABASE_ECHO"] = ""
    elif mode == "empty-refresh-ttl":
        values["GAME_REFRESH_TOKEN_EXPIRE_MINUTES"] = ""
    elif mode == "empty-stream-maxlen":
        values["GAME_STREAM_MAXLEN"] = ""
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
    assert result.returncode == 0, "Sanitized System Compose config failed"
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
import socket
def forbid_connection(*args, **kwargs):
    raise AssertionError('Worker import must not connect to a network')
socket.socket.connect = forbid_connection
socket.socket.connect_ex = forbid_connection
socket.create_connection = forbid_connection
original = pydantic_settings.SettingsConfigDict
def without_dotenv(*args, **kwargs):
    kwargs['env_file'] = None
    return original(*args, **kwargs)
pydantic_settings.SettingsConfigDict = without_dotenv
import src.backend.core.arq_logging as worker_logging
worker_logging.setup_logging = lambda *a, **k: None
from src.backend.features.combat.workers.arq import CombatArqSettings as Worker
from src.backend.config.runtime import runtime_settings as settings
from src.backend.features.combat.workers.arq import COMBAT_TASKS
assert Worker.redis_settings.host == 'cache.invalid'
assert Worker.queue_name == 'tbmmorpg:arq:combat'
assert Worker.functions == COMBAT_TASKS
assert Worker.max_jobs == 30
assert Worker.job_timeout == 60
assert Worker.keep_result == 0
assert Worker.on_startup.__name__ == 'combat_startup'
assert Worker.on_shutdown.__name__ == 'combat_shutdown'
assert len(Worker.functions) == 7
from pathlib import Path
from src.backend.features.combat.runtime.ai.policy_store import PolicyStore
assert PolicyStore._resolve_path(None) == (
    Path(settings.combat_ai_policy_path) if settings.combat_ai_policy_path else
    Path(__import__('src.backend.features.combat.runtime.ai.policy_store', fromlist=['_DEFAULT_POLICY_PATH'])._DEFAULT_POLICY_PATH)
)
from src.backend.infrastructure.actor_state.managers.game_session_lock import GameSessionLockManager
assert GameSessionLockManager(None).ttl_seconds == max(60, settings.game_refresh_token_expire_minutes * 60)
from src.backend.features.character.models.symbiote import CharacterSymbiote
assert CharacterSymbiote.__table__.c.symbiote_name.default.arg == settings.default_symbiote_name
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
    if mode in {"empty-timeout", "empty-echo", "empty-stream-maxlen", "empty-refresh-ttl"}:
        assert parsed.returncode != 0
        field = {
            "empty-timeout": "mongo_server_selection_timeout_ms",
            "empty-echo": "database_echo",
            "empty-stream-maxlen": "game_stream_maxlen",
            "empty-refresh-ttl": "game_refresh_token_expire_minutes",
        }[mode]
        assert field in parsed.stderr
        return
    assert parsed.returncode == 0, "Actual Combat worker rejected sanitized resolved config: " + parsed.stderr
    settings = json.loads(parsed.stdout)
    assert settings["debug"] is False
    assert settings["database_url"] == values["GAME_DATABASE_URL"]
    assert settings["mongo_url"] == values["MONGO_URL"]
    for key in ("log_level_console", "log_level_file", "log_rotation", "log_dir"):
        if mode in {"overrides", "empty"}:
            assert settings[key] == values[key.upper()]
    assert settings["database_echo"] is (mode == "overrides")
    assert settings["mongo_server_selection_timeout_ms"] == (1234 if mode == "overrides" else 5000)
    assert settings["mongo_database"] == ("synthetic_combat" if mode == "overrides" else "tbmmorpg_analytics")
    assert settings["gemini_api_key"] is None
    assert settings["default_symbiote_name"] == values.get("DEFAULT_SYMBIOTE_NAME", "SYSTEM")
    assert settings["game_stream_name"] == values.get("GAME_STREAM_NAME", "game_events")
    assert settings["game_stream_maxlen"] == int(values.get("GAME_STREAM_MAXLEN", "10000"))
    assert settings["combat_ai_policy_path"] == values.get("COMBAT_AI_POLICY_PATH")
    assert (
        not {
            "secret_key",
            "frontend_internal_service_key",
            "site_to_game_service_key",
            "site_database_url",
            "asset_s3_secret_access_key",
            "operator_write_key",
        }
        & settings.keys()
    )
    assert settings["game_refresh_token_expire_minutes"] == int(values.get("GAME_REFRESH_TOKEN_EXPIRE_MINUTES", "720"))
