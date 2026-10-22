"""Production bot receives its own settings, never the complete deployment env."""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy/compose.tg-bot.yml"
REQUIRED = {
    "DOCKER_IMAGE_TG_BOT": "fake.invalid/bot:test",
    "BOT_TOKEN": "123456:synthetic-token",
    "TELEGRAM_CHANNEL_ID": "-10012345",
    "DOMAIN_NAME": "example.test",
    "SECRET_KEY": "synthetic-bot-secret",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "REDIS_URL": "redis://cache.invalid:6379/0",
}
CANARIES = {
    "POSTGRES_PASSWORD": "canary-postgres",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "DATABASE_URL": "postgresql://canary:canary@db.invalid/game",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "SITE_DATABASE_URL": "postgresql://canary:canary@db.invalid/site",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "MONGO_URI": "mongodb://canary:canary@mongo.invalid/",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "MONGO_URL": "mongodb://canary:canary@mongo.invalid/current",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "GAME_DATABASE_URL": "postgresql://canary:canary@db.invalid/current",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "GEMINI_API_KEY": "canary-gemini",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "ASSET_S3_SECRET_ACCESS_KEY": "canary-assets",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "FRONTEND_INTERNAL_SERVICE_KEY": "canary-site-service",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "MONGO_INITDB_ROOT_PASSWORD": "canary-mongo-root",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "AI_API_KEY": "canary-ai",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "OPENAI_API_KEY": "canary-openai",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "S3_SECRET_ACCESS_KEY": "canary-s3",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "SMTP_PASSWORD": "canary-smtp",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "OPERATOR_WRITE_KEY": "canary-operator",  # pragma: allowlist secret - synthetic credential canary, never a real secret
    "OTHER_SECRET": "canary-new-setting",  # pragma: allowlist secret - synthetic credential canary, never a real secret
}


def test_bot_has_explicit_settings_allowlist():
    bot = yaml.safe_load(COMPOSE.read_text())["services"]["tg-bot"]
    assert "env_file" not in bot
    assert not set(CANARIES) & bot["environment"].keys()
    # An added BotSettings field requires an explicit decision here/at deployment.
    from tg_bot.core.config import BotSettings

    aliases = set()
    for name, field in BotSettings.model_fields.items():
        alias = field.validation_alias or field.alias or name
        aliases.add(alias.choices[0] if hasattr(alias, "choices") else alias)
    assert set(bot["environment"]) == aliases


@pytest.mark.external
@pytest.mark.parametrize("mode", ["defaults", "overrides", "empty"])
def test_resolved_bot_env_is_isolated_and_settings_compatible(tmp_path, mode):
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("Docker Compose CLI required; no containers are started")
    values = dict(REQUIRED, **CANARIES)
    if mode == "overrides":
        values.update(
            BACKEND_BASE_URL="http://synthetic-backend:8080",
            BACKEND_API_KEY="synthetic-service-key",  # pragma: allowlist secret - synthetic credential canary, never a real secret
            BACKEND_API_TIMEOUT="2.5",
            BOT_THROTTLING_RATE="0.5",
            BOT_ALLOWED_UPDATES='["callback_query"]',
            SUPERUSER_IDS="101,202",
            OWNER_IDS="303",
            LOG_LEVEL_CONSOLE="WARNING",
            LOG_LEVEL_FILE="ERROR",
            LOG_ROTATION="20 MB",
            LOG_DIR="synthetic-logs",
            GAME_STREAM_NAME="synthetic-events",
            # These were overridden by explicit production values before isolation.
            USE_REDIS="False",
            DEBUG="True",
            REDIS_CONSUMER_GROUP="ignored-group",
        )
    elif mode == "empty":
        values.update(
            BACKEND_API_KEY="",
            BACKEND_BASE_URL="",
            LOG_LEVEL_CONSOLE="",
            LOG_LEVEL_FILE="",
            LOG_ROTATION="",
            LOG_DIR="",
            SUPERUSER_IDS="",
            OWNER_IDS="",
            BOT_ALLOWED_UPDATES="[]",
        )
    fake_env = tmp_path / "synthetic.env"
    fake_env.write_text("".join(f"{key}='{value}'\n" for key, value in values.items()))
    # Preserve Docker CLI/plugin discovery, but remove every Compose/settings input.
    # Explicit --env-file prevents automatic repository .env loading.
    environment = os.environ.copy()
    names = set(CANARIES) | set(REQUIRED)
    names.update(yaml.safe_load(COMPOSE.read_text())["services"]["tg-bot"]["environment"])
    for path in (ROOT / "deploy").glob("*.yml"):
        names.update(re.findall(r"\$\{([A-Z][A-Z0-9_]*)", path.read_text()))
    for name in names | {"PYTHONPATH", "COMPOSE_FILE", "COMPOSE_ENV_FILES", "COMPOSE_PROJECT_NAME"}:
        environment.pop(name, None)
    result = subprocess.run(
        [docker, "compose", "--env-file", str(fake_env), "-f", str(COMPOSE), "config", "--format", "json"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, "Sanitized bot Compose config failed"
    bot = json.loads(result.stdout)["services"]["tg-bot"]
    resolved = bot["environment"]
    assert not set(CANARIES) & resolved.keys()
    assert not any(value in json.dumps(bot) for value in CANARIES.values())
    assert resolved["SECRET_KEY"] == REQUIRED["SECRET_KEY"]
    assert resolved["USE_REDIS"] == "True"
    assert resolved["USE_REDIS_FSM"] == "True"
    assert resolved["USE_REDIS_STREAMS"] == "True"
    assert resolved["DEBUG"] == "False"
    assert resolved["REDIS_CONSUMER_GROUP"] == "tg_bot"

    # Fresh process avoids test-process settings caches and explicitly disables .env.
    script = """
import json
from tg_bot.core.config import BotSettings
settings = BotSettings(_env_file=None)
print(settings.model_dump_json())
"""
    parsed = subprocess.run(
        [sys.executable, "-c", script],
        env=dict(environment, PYTHONPATH=str(ROOT / "src"), **{k: v for k, v in resolved.items() if v is not None}),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert parsed.returncode == 0, "BotSettings rejected sanitized resolved config"
    settings = json.loads(parsed.stdout)
    assert settings["debug"] is False
    assert settings["use_redis"] is True
    if mode == "defaults":
        assert settings["backend_api_key"] is None
        assert settings["log_level_console"] == "INFO"
        assert settings["backend_api_timeout"] == 10.0
        assert settings["bot_throttling_rate"] == 1.0
        assert settings["bot_allowed_updates"] == ["message", "callback_query", "inline_query"]
        assert settings["redis_stream_name"] == "game_events"
    elif mode == "overrides":
        assert settings["backend_api_key"] == values["BACKEND_API_KEY"]
        assert settings["backend_base_url"] == values["BACKEND_BASE_URL"]
        assert settings["backend_api_timeout"] == 2.5
        assert settings["bot_throttling_rate"] == 0.5
        assert settings["bot_allowed_updates"] == ["callback_query"]
        assert settings["superuser_ids"] == "101,202"
        assert settings["owner_ids"] == "303"
        for key in ("log_level_console", "log_level_file", "log_rotation", "log_dir"):
            assert settings[key] == values[key.upper()]
        assert settings["redis_stream_name"] == "synthetic-events"
    else:
        assert settings["backend_api_key"] == ""
        assert settings["backend_base_url"] == "http://backend:8001"
        assert settings["log_level_console"] == "INFO"
        assert settings["bot_allowed_updates"] == []
        for key in ("log_level_file", "log_rotation", "log_dir", "superuser_ids", "owner_ids"):
            assert settings[key] == ""
