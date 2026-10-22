"""Backend application receives a bounded environment without reading deployment secrets."""

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
SERVICE = "backend"
ALLOWLIST = {
    "DEFAULT_SYMBIOTE_NAME",
    "GAME_ACCESS_TOKEN_EXPIRE_MINUTES",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "SITE_TO_GAME_SERVICE_KEY",
    "WORLD_AUTO_GENERATE",
    "GAME_STREAM_NAME",
    "GAME_REFRESH_TOKEN_EXPIRE_MINUTES",
    "GEMINI_API_KEY",
    "OPERATOR_WRITE_KEY",
    "SECRET_KEY",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "STREAM_PENDING_MIN_IDLE_MS",
    "ENABLE_DEV_RIFT_ROUTES",
    "DATABASE_ECHO",
    "WORKER_NAME",
    "DATABASE_URL",
    "COMBAT_AI_POLICY_PATH",
    "FRONTEND_INTERNAL_SERVICE_KEY",
    "AUTHX_JWT_TOKEN_LOCATIONS",
    "GEMINI_MODEL",
    "MONSTER_CATALOG_READ_KEY",
    "MONGO_SERVER_SELECTION_TIMEOUT_MS",
    "LOG_DIR",
    "GAME_STREAM_MAXLEN",
    "MONGO_URL",
    "WORLD_GENERATION_MODE",
    "REDIS_URL",
    "LOG_LEVEL_FILE",
    "STREAM_CONSUMER_GROUP",
    "AUTHX_JWT_ALGORITHM",
    "LOG_LEVEL_CONSOLE",
    "LOG_ROTATION",
    "MONGO_DATABASE",
    "DEBUG",
    "STREAM_ENABLED_GROUPS",
    "GAME_DATABASE_URL",
    "MONSTER_CATALOG_WRITE_KEY",
    "OPERATOR_READ_KEY",
    "STREAM_PENDING_SCAN_COUNT",
    "REALTIME_ALLOWED_ORIGINS",
}
# These credentials still transit through shared BackendSettings; role separation is deferred.
EXCLUDED = set(CANARIES) - {
    "DATABASE_URL",
    "GAME_DATABASE_URL",
    "MONGO_URL",
    "FRONTEND_INTERNAL_SERVICE_KEY",
    "GEMINI_API_KEY",
    "OPERATOR_WRITE_KEY",
}


def test_backend_environment_is_an_explicit_allowlist():
    service = yaml.safe_load(COMPOSE.read_text())["services"][SERVICE]
    assert "env_file" not in service
    assert set(service["environment"]) == ALLOWLIST
    assert not EXCLUDED & service["environment"].keys()
    assert service["entrypoint"][:2] == ["uvicorn", "src.backend.app:app"]


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
        "empty-origins",
        "csv-origins",
        "missing-gemini",
        "empty-world-mode",
        "empty-maxlen",
        "empty-locations",
        "partial-group",
        "invalid-group",
        "empty-refresh-ttl",
    ],
)
def test_backend_resolved_environment_and_actual_app_import(tmp_path, mode):
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
        REALTIME_ALLOWED_ORIGINS='["https://backend.example.test"]',
    )
    if mode == "overrides":
        values.update(
            DATABASE_ECHO="True",
            MONGO_SERVER_SELECTION_TIMEOUT_MS="1234",
            LOG_LEVEL_CONSOLE="WARNING",
            LOG_LEVEL_FILE="ERROR",
            LOG_ROTATION="20 MB",
            LOG_DIR="synthetic-logs",
            MONGO_DATABASE="synthetic_backend",
            ACCESS_TOKEN_EXPIRE_MINUTES="41",
            REFRESH_TOKEN_EXPIRE_DAYS="9",
            AUTHX_JWT_ALGORITHM="HS256",
            AUTHX_JWT_TOKEN_LOCATIONS='["cookies","headers"]',
            GAME_ACCESS_TOKEN_EXPIRE_MINUTES="11",
            STREAM_PENDING_MIN_IDLE_MS="12345",
            STREAM_PENDING_SCAN_COUNT="19",
            STREAM_CONSUMER_GROUP="synthetic_backend_group",
            WORKER_NAME="synthetic_backend_worker",
            STREAM_ENABLED_GROUPS='["world","combat"]',
            GAME_STREAM_MAXLEN="789",
            DEFAULT_SYMBIOTE_NAME="synthetic-symbiote",
            WORLD_AUTO_GENERATE="True",
            WORLD_GENERATION_MODE="full",
            ENABLE_DEV_RIFT_ROUTES="False",
            GEMINI_MODEL="synthetic-model",
            COMBAT_AI_POLICY_PATH="synthetic-policy.json",
            MONSTER_CATALOG_READ_KEY="synthetic-read",  # pragma: allowlist secret - synthetic fixture
            MONSTER_CATALOG_WRITE_KEY="synthetic-write",  # pragma: allowlist secret - synthetic fixture
            OPERATOR_READ_KEY="synthetic-ops-read",  # pragma: allowlist secret - synthetic fixture
            OPERATOR_WRITE_KEY="synthetic-ops-write",  # pragma: allowlist secret - synthetic fixture
            GAME_REFRESH_TOKEN_EXPIRE_MINUTES="123",
            GAME_STREAM_NAME="synthetic_events",
        )
    elif mode == "empty":
        values.update(
            GAME_STREAM_NAME="",
            STREAM_CONSUMER_GROUP="",
            WORKER_NAME="",
            DEFAULT_SYMBIOTE_NAME="",
            GEMINI_API_KEY="",
            GEMINI_MODEL="",
            COMBAT_AI_POLICY_PATH="",
            MONSTER_CATALOG_READ_KEY="",
            MONSTER_CATALOG_WRITE_KEY="",
            OPERATOR_READ_KEY="",
            OPERATOR_WRITE_KEY="",
        )
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
    elif mode == "empty-origins":
        values["REALTIME_ALLOWED_ORIGINS"] = ""
    elif mode == "csv-origins":
        values["REALTIME_ALLOWED_ORIGINS"] = "https://backend.example.test,https://other.example.test"
    elif mode == "missing-gemini":
        values.pop("GEMINI_API_KEY", None)
    elif mode == "empty-world-mode":
        values["WORLD_GENERATION_MODE"] = ""
    elif mode == "empty-maxlen":
        values["GAME_STREAM_MAXLEN"] = ""
    elif mode == "empty-locations":
        values["AUTHX_JWT_TOKEN_LOCATIONS"] = ""
    elif mode == "invalid-group":
        values["STREAM_ENABLED_GROUPS"] = '["chat"]'
        values["STREAM_CONSUMER_GROUP"] = "monolith"
    elif mode == "partial-group":
        values["STREAM_ENABLED_GROUPS"] = '["world"]'
        values["STREAM_CONSUMER_GROUP"] = "synthetic_backend"
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
    assert result.returncode == 0, "Sanitized chat Compose config failed"
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
    raise AssertionError('Backend import must not connect to a network')
socket.socket.connect = forbid_connection
socket.socket.connect_ex = forbid_connection
socket.create_connection = forbid_connection
original = pydantic_settings.SettingsConfigDict
def without_dotenv(*args, **kwargs):
    kwargs['env_file'] = None
    return original(*args, **kwargs)
pydantic_settings.SettingsConfigDict = without_dotenv
import src.shared.infrastructure.logging_config as log_config
log_config.setup_logging = lambda *a, **k: None
from src.backend.app import app
from src.backend.config.settings import settings
from src.backend.core.security import authx
from datetime import timedelta
routes = {route.path for route in app.routes}
assert {'/health','/metrics','/api/admin/generation-ai/tasks/{task_id}'} <= routes
assert authx.config.JWT_ALGORITHM == settings.authx_jwt_algorithm
assert authx.config.JWT_TOKEN_LOCATION == settings.authx_jwt_token_locations
assert authx.config.JWT_ACCESS_TOKEN_EXPIRES == timedelta(minutes=settings.access_token_expire_minutes)
assert authx.config.JWT_REFRESH_TOKEN_EXPIRES == timedelta(days=settings.refresh_token_expire_days)
from src.backend.infrastructure.actor_state.managers.game_session_lock import GameSessionLockManager
assert GameSessionLockManager(None).ttl_seconds == max(60, settings.game_refresh_token_expire_minutes * 60)
from src.backend.features.character.models.symbiote import CharacterSymbiote
assert CharacterSymbiote.__table__.c.symbiote_name.default.arg == settings.default_symbiote_name
from src.backend.core.operator_auth import _keys
assert _keys() == (settings.operator_read_key, settings.operator_write_key)
import src.backend.core.ai as ai
calls = []
class FakeProvider:
    def __init__(self, **kwargs): calls.append(kwargs)
ai.GeminiProvider = FakeProvider
service = ai.AIService()
assert calls == ([{'api_key': settings.gemini_api_key, 'model': settings.gemini_model}]
                 if settings.gemini_api_key else [])
import os
import src.backend.features.combat.runtime.ai.policy_store as policy_module
from src.backend.config.settings import _BUNDLED_TRAINED_COMBAT_AI_POLICY
from pathlib import Path
if settings.combat_ai_policy_path:
    expected = Path(settings.combat_ai_policy_path)
elif os.environ.get('COMBAT_AI_POLICY_PATH'):
    expected = _BUNDLED_TRAINED_COMBAT_AI_POLICY
else:
    expected = policy_module._DEFAULT_POLICY_PATH
assert policy_module.PolicyStore._resolve_path(None) == expected
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
    if mode in {
        "empty-timeout",
        "empty-echo",
        "empty-refresh-ttl",
        "empty-world-mode",
        "empty-maxlen",
        "empty-locations",
        "empty-origins",
        "csv-origins",
    }:
        assert parsed.returncode != 0
        field = {
            "empty-timeout": "mongo_server_selection_timeout_ms",
            "empty-echo": "database_echo",
            "empty-world-mode": "world_generation_mode",
            "empty-maxlen": "game_stream_maxlen",
            "empty-locations": "authx_jwt_token_locations",
            "empty-origins": "realtime_allowed_origins",
            "csv-origins": "realtime_allowed_origins",
            "empty-refresh-ttl": "game_refresh_token_expire_minutes",
        }[mode]
        assert field in parsed.stderr
        return
    if mode == "invalid-group":
        assert parsed.returncode != 0
        assert "Partial enabled_groups" in parsed.stderr
        return
    if mode in {"invalid-secrets", "invalid-service", "missing-auth"}:
        assert parsed.returncode != 0
        assert "Production settings cannot use default or development secret keys" in parsed.stderr
        return
    assert parsed.returncode == 0, "Actual Backend application rejected sanitized resolved config: " + parsed.stderr
    settings = json.loads(parsed.stdout)
    assert settings["debug"] is False
    assert settings["database_url"] == values["GAME_DATABASE_URL"]
    assert settings["mongo_url"] == values["MONGO_URL"]
    for key in ("log_level_console", "log_level_file", "log_rotation", "log_dir"):
        if mode in {"overrides", "empty"}:
            assert settings[key] == values[key.upper()]
    assert settings["database_echo"] is (mode == "overrides")
    assert settings["mongo_server_selection_timeout_ms"] == (1234 if mode == "overrides" else 5000)
    assert settings["mongo_database"] == ("synthetic_backend" if mode == "overrides" else "tbmmorpg_analytics")
    assert settings["gemini_api_key"] == (None if mode == "missing-gemini" else values["GEMINI_API_KEY"])
    assert settings["gemini_model"] == values.get("GEMINI_MODEL", "gemini-2.5-flash")
    assert settings["game_stream_name"] == values.get("GAME_STREAM_NAME", "game_events")
    assert settings["site_database_url"] != values["SITE_DATABASE_URL"]
    assert settings["asset_s3_secret_access_key"] is None
    for key in ("monster_catalog_read_key", "monster_catalog_write_key", "operator_read_key", "operator_write_key"):
        assert settings[key] == values.get(key.upper(), "")
    assert settings["game_refresh_token_expire_minutes"] == int(values.get("GAME_REFRESH_TOKEN_EXPIRE_MINUTES", "720"))
    for key, default in {
        "access_token_expire_minutes": 30,
        "refresh_token_expire_days": 30,
        "game_access_token_expire_minutes": 15,
        "stream_pending_min_idle_ms": 300000,
        "stream_pending_scan_count": 100,
        "game_stream_maxlen": 10000,
    }.items():
        assert settings[key] == int(values.get(key.upper(), default))
    assert settings["stream_consumer_group"] == values.get("STREAM_CONSUMER_GROUP", "monolith")
    assert settings["worker_name"] == values.get("WORKER_NAME", "worker_1")
    assert (
        settings["stream_enabled_groups"] == json.loads(values["STREAM_ENABLED_GROUPS"])
        if "STREAM_ENABLED_GROUPS" in values
        else settings["stream_enabled_groups"] is None
    )
    assert settings["default_symbiote_name"] == values.get("DEFAULT_SYMBIOTE_NAME", "SYSTEM")
    assert settings["world_auto_generate"] is (mode == "overrides")
    assert settings["world_generation_mode"] == values.get("WORLD_GENERATION_MODE", "test")
    assert settings["enable_dev_rift_routes"] is (mode != "overrides")
