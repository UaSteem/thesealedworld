"""Play frontend receives explicit settings; all credentials here are synthetic."""

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
from tests.deploy.test_bot_env_isolation import CANARIES as BOT_CANARIES

CANARIES = dict(
    BOT_CANARIES, BACKEND_OPERATOR_READ_KEY="canary-frontend-read", BACKEND_OPERATOR_WRITE_KEY="canary-frontend-write"
)  # pragma: allowlist secret - synthetic fixtures

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "deploy/compose.site.yml"
ALLOWLIST = {
    "TEMPLATES_DIR",
    "ASSET_S3_SECRET_ACCESS_KEY",
    "LOG_LEVEL_FILE",
    "GENERATED_ASSETS_DIR",
    "BACKEND_INTERNAL_SERVICE_KEY",
    "CSRF_HEADER_NAME",
    "ENABLE_DEV_RIFT_ROUTES",
    "DATABASE_ECHO",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "SITE_NAME",
    "ASSET_S3_ACCESS_KEY_ID",
    "SITE_META_TITLE",
    "ASSET_STORAGE_BACKEND",
    "SECRET_KEY",
    "SITE_META_DESCRIPTION",
    "ASSET_S3_ENDPOINT_URL",
    "SITE_BASE_URL",
    "AUTH_COOKIE_DOMAIN",
    "ACTIVE_CHARACTER_COOKIE_SECURE",
    "ASSET_S3_BUCKET",
    "CSRF_COOKIE_NAME",
    "CSRF_FIELD_NAME",
    "AUTH_COOKIE_SECURE",
    "DEFAULT_SYMBIOTE_NAME",
    "SITE_META_IMAGE",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "GOOGLE_SITE_VERIFICATION",
    "LOG_LEVEL_CONSOLE",
    "LOG_ROTATION",
    "BACKEND_BASE_URL",
    "LOG_DIR",
    "DATABASE_URL",
    "ASSET_S3_REGION",
    "DEBUG",
    "REALTIME_WS_URL",
    "PYTHONPATH",
    "BACKEND_INTERNAL_SERVICE_HEADER",
    "GOOGLE_TAG_MANAGER_ID",
    "RELEASE_STAGE",
    "RELEASE_PROGRESS_POLICY",
    "FRONTEND_SURFACE",
    "SITE_DATABASE_URL",
    "RELEASE_VERSION",
    "AUTHX_JWT_TOKEN_LOCATIONS",
    "GAME_TOKEN_COOKIE_SECURE",
    "GOOGLE_ANALYTICS_ID",
    "STATIC_DIR",
    "AUTHX_JWT_ALGORITHM",
}
EXCLUDED = set(CANARIES) - {"DATABASE_URL", "SITE_DATABASE_URL", "ASSET_S3_SECRET_ACCESS_KEY"}
EXCLUDED |= {"REDIS_URL", "SMTP_PASSWORD", "BACKEND_OPERATOR_READ_KEY", "BACKEND_OPERATOR_WRITE_KEY"}


def test_frontend_play_environment_is_explicit():
    services = yaml.safe_load(COMPOSE.read_text())["services"]
    service = services["frontend-play"]
    assert "env_file" not in service
    assert set(service["environment"]) == ALLOWLIST
    assert not EXCLUDED & service["environment"].keys()
    assert service["environment"]["FRONTEND_SURFACE"] == "play"
    assert service["entrypoint"] == [
        "uvicorn",
        "src.frontend.app:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--log-level",
        "info",
    ]


@pytest.mark.external
@pytest.mark.parametrize(
    "mode",
    [
        "defaults",
        "overrides",
        "s3",
        "missing-s3",
        "empty",
        "missing-auth",
        "invalid-secret",
        "invalid-service",
        "empty-game-cookie",
        "empty-active-cookie",
        "empty-locations",
        "invalid-stage",
        "invalid-storage",
        "realtime-empty",
    ],
)
def test_frontend_play_resolved_environment_and_actual_app_import(tmp_path, mode):
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
        REDIS_URL="redis://cache.invalid:6379/0",
        SECRET_KEY="synthetic-production-key",  # pragma: allowlist secret - synthetic fixture
        BACKEND_INTERNAL_SERVICE_KEY="synthetic-service-key",  # pragma: allowlist secret - synthetic fixture
        SITE_BASE_URL="https://site.example.test",
        PLAY_PUBLIC_BASE_URL="https://play.example.test",
        AUTH_COOKIE_DOMAIN=".example.test",
        GENERATED_ASSETS_DIR=str(tmp_path / "generated"),
        DEBUG="True",
    )
    if mode == "overrides":
        values.update(
            BACKEND_BASE_URL="https://api.example.test/",
            REALTIME_WS_URL="wss://realtime.example.test/custom",
            ACTIVE_CHARACTER_COOKIE_SECURE="true",
            GAME_TOKEN_COOKIE_SECURE="true",
            DEFAULT_SYMBIOTE_NAME="synthetic-symbiote",
            ENABLE_DEV_RIFT_ROUTES="false",
            PLAY_INTERNAL_BASE_URL="http://play.invalid:8000",
            PLAY_HEALTH_TIMEOUT_SECONDS="2.5",
            BACKEND_INTERNAL_SERVICE_HEADER="X-Synthetic-Service",
            BACKEND_OPERATOR_READ_KEY="synthetic-ops-read",
            BACKEND_OPERATOR_WRITE_KEY="synthetic-ops-write",  # pragma: allowlist secret - synthetic fixtures
            AUTH_COOKIE_SECURE="true",
            AUTH_USER_CACHE_TTL_SECONDS="456",
            ENABLE_EMAIL_VERIFICATION="true",
            CSRF_COOKIE_NAME="synthetic_csrf",
            CSRF_HEADER_NAME="X-Synthetic-CSRF",
            CSRF_FIELD_NAME="synthetic_csrf_field",
            RELEASE_STAGE="beta",
            RELEASE_VERSION="9.8.7",
            RELEASE_PROGRESS_POLICY="synthetic policy",
            DATABASE_ECHO="true",
            ACCESS_TOKEN_EXPIRE_MINUTES="42",
            REFRESH_TOKEN_EXPIRE_DAYS="9",
            AUTHX_JWT_ALGORITHM="HS384",
            AUTHX_JWT_TOKEN_LOCATIONS='["cookies","headers"]',
            SMTP_HOST="smtp.invalid",
            SMTP_PORT="2525",
            SMTP_START_TLS="false",
            SMTP_USER="synthetic-user",
            SMTP_PASSWORD="synthetic-smtp-password",  # pragma: allowlist secret - synthetic fixture
            EMAIL_FROM="from@example.test",
            EMAIL_ADMIN="admin@example.test",  # pragma: allowlist secret - synthetic fixture
            SITE_NAME="Synthetic Site",
            SITE_META_TITLE="Synthetic title",
            SITE_META_DESCRIPTION="Synthetic description",
            SITE_META_IMAGE="/static/synthetic.webp",
            GOOGLE_TAG_MANAGER_ID="GTM-SYNTHETIC",
            GOOGLE_ANALYTICS_ID="G-SYNTHETIC",
            GOOGLE_SITE_VERIFICATION="synthetic-verification",
            LOG_LEVEL_CONSOLE="WARNING",
            LOG_LEVEL_FILE="ERROR",
            LOG_ROTATION="20 MB",
            LOG_DIR="synthetic-logs",
            ASSET_PUBLIC_BASE_URL="/synthetic-assets",
            ASSET_LOCAL_ROOT="synthetic-assets",
        )
    elif mode in {"s3", "missing-s3"}:
        values.update(
            ASSET_STORAGE_BACKEND="s3",
            ASSET_S3_BUCKET="synthetic-bucket",
            ASSET_S3_REGION="synthetic-region",
            ASSET_S3_ENDPOINT_URL="https://s3.example.test",
            ASSET_S3_ACCESS_KEY_ID="synthetic-s3-id",
        )  # pragma: allowlist secret - synthetic fixture
        if mode == "missing-s3":
            values.pop("ASSET_S3_SECRET_ACCESS_KEY")
    elif mode == "empty":
        values.update(
            SMTP_USER="",
            SMTP_PASSWORD="",
            EMAIL_ADMIN="",
            SITE_NAME="",
            SITE_META_TITLE="",  # pragma: allowlist secret - synthetic fixture
            LOG_LEVEL_CONSOLE="",
            LOG_LEVEL_FILE="",
            LOG_ROTATION="",
            LOG_DIR="",
            BACKEND_OPERATOR_READ_KEY="",
            BACKEND_OPERATOR_WRITE_KEY="",
        )
    elif mode == "missing-auth":
        values["BACKEND_INTERNAL_SERVICE_KEY"] = ""
    elif mode == "invalid-secret":
        values["SECRET_KEY"] = "dev-rejected"  # pragma: allowlist secret - synthetic fixture
    elif mode == "invalid-service":
        values["BACKEND_INTERNAL_SERVICE_KEY"] = "dev-rejected"  # pragma: allowlist secret - synthetic fixture
    elif mode == "empty-game-cookie":
        values["GAME_TOKEN_COOKIE_SECURE"] = ""
    elif mode == "empty-active-cookie":
        values["ACTIVE_CHARACTER_COOKIE_SECURE"] = ""
    elif mode == "empty-locations":
        values["AUTHX_JWT_TOKEN_LOCATIONS"] = ""
    elif mode == "invalid-stage":
        values["RELEASE_STAGE"] = "invalid"
    elif mode == "realtime-empty":
        values["REALTIME_WS_URL"] = ""
    elif mode == "invalid-storage":
        values["ASSET_STORAGE_BACKEND"] = "invalid"
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
        | fields
        | set(CANARIES)
        | ALLOWLIST
        | {
            "PYTHONPATH",
            "COMPOSE_FILE",
            "COMPOSE_ENV_FILES",
            "COMPOSE_PROJECT_NAME",
            "REDIS_HOST",
            "REDIS_PORT",
            "REDIS_PASSWORD",
            "REDIS_MAX_CONNECTIONS",
            "REDIS_TIMEOUT",
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
    if mode == "missing-auth":
        assert result.returncode != 0
        assert "BACKEND_INTERNAL_SERVICE_KEY" in result.stderr
        return
    assert result.returncode == 0, "Sanitized frontend-play Compose resolution failed"
    service = json.loads(result.stdout)["services"]["frontend-play"]
    resolved = service["environment"]
    assert set(resolved) == ALLOWLIST
    assert not EXCLUDED & resolved.keys()
    assert not any(value in json.dumps(service) for key, value in CANARIES.items() if key in EXCLUDED)
    assert resolved["DATABASE_URL"] == values["SITE_DATABASE_URL"]
    assert "REDIS_URL" not in resolved
    assert resolved["PYTHONPATH"] == "/app:/app/src"
    assert resolved["FRONTEND_SURFACE"] == "play"
    script = r"""
import json, socket, pydantic_settings
from pathlib import Path
from types import SimpleNamespace
from datetime import timedelta
def forbid_connection(*args, **kwargs):
    raise AssertionError('Frontend import must not connect to a network')
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
from src.frontend.app import app
from src.frontend.config.settings import settings
paths = {route.path for route in app.routes}
assert {'/health', '/metrics', '/game-lobby', '/game/session'} <= paths
assert '/login' not in paths and '/account' not in paths and not any(path.startswith('/admin') for path in paths)
assert settings.frontend_surface == 'play' and settings.debug is False
from src.frontend.features.auth.security.authx_config import build_authx_config
cfg = build_authx_config(settings)
assert cfg.JWT_ALGORITHM == settings.authx_jwt_algorithm
assert cfg.JWT_TOKEN_LOCATION == settings.authx_jwt_token_locations
assert cfg.JWT_ACCESS_TOKEN_EXPIRES == timedelta(minutes=settings.access_token_expire_minutes)
assert cfg.JWT_REFRESH_TOKEN_EXPIRES == timedelta(days=settings.refresh_token_expire_days)
from src.frontend.features.auth.services.auth_service import FrontendAuthService
from starlette.responses import Response
from http.cookies import SimpleCookie
response = Response()
FrontendAuthService.attach_auth_cookies(FrontendAuthService.__new__(FrontendAuthService), response, SimpleNamespace(access_token='synthetic-access', refresh_token='synthetic-refresh'))
cookies = SimpleCookie()
for header in response.headers.getlist('set-cookie'):
    cookies.load(header)
assert len(cookies) == 2
assert all(bool(cookie['secure']) == settings.auth_cookie_secure and cookie['domain'] == settings.auth_cookie_domain for cookie in cookies.values())
from src.frontend.core.csrf import _build_set_cookie
assert ('; Secure' in _build_set_cookie(settings.csrf_cookie_name, 'synthetic-csrf')) == settings.auth_cookie_secure
from src.frontend.game_features.session.cookies import set_active_character_cookie, ACTIVE_CHARACTER_COOKIE
from src.frontend.game_features.session.token_state import set_game_token_cookies
response = Response()
set_active_character_cookie(response, 123)
set_game_token_cookies(response, access_token='synthetic-game-access', refresh_token='synthetic-game-refresh')
cookies = SimpleCookie()
for header in response.headers.getlist('set-cookie'):
    cookies.load(header)
assert len(cookies) == 3
assert bool(cookies[ACTIVE_CHARACTER_COOKIE]['secure']) == settings.active_character_cookie_secure
assert all(bool(cookie['secure']) == settings.game_token_cookie_secure and cookie['domain'] == settings.auth_cookie_domain for name,cookie in cookies.items() if name != ACTIVE_CHARACTER_COOKIE)
from src.frontend.core.api import BaseApiClient
api = BaseApiClient(None, settings.backend_base_url)
assert api.base_url == settings.backend_base_url.rstrip('/')
assert api.internal_service_key == settings.backend_internal_service_key
assert api.internal_service_header == settings.backend_internal_service_header
from src.frontend.integrations.generated_assets import build_s3_generated_asset_reader
if settings.asset_storage_backend == 's3':
    if settings.asset_s3_secret_access_key:
        import boto3
        calls = []
        boto3.client = lambda *a, **k: (calls.append((a,k)) or SimpleNamespace(meta=SimpleNamespace(endpoint_url=settings.asset_s3_endpoint_url)))
        reader = build_s3_generated_asset_reader(settings)
        assert reader.bucket == settings.asset_s3_bucket
        assert calls == [(('s3',), dict(region_name=settings.asset_s3_region, endpoint_url=settings.asset_s3_endpoint_url, aws_access_key_id=settings.asset_s3_access_key_id, aws_secret_access_key=settings.asset_s3_secret_access_key))]
    else:
        try:
            build_s3_generated_asset_reader(settings)
        except RuntimeError as exc:
            assert 'ASSET_S3_SECRET_ACCESS_KEY' in str(exc)
        else:
            raise AssertionError('Missing S3 credentials must fail before SDK use')
print(settings.model_dump_json())
"""
    parsed = subprocess.run(
        [sys.executable, "-c", script],
        env={
            **environment,
            **{k: v for k, v in resolved.items() if v is not None},
            "PYTHONPATH": os.pathsep.join([str(ROOT), str(ROOT / "src")]),
        },
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=45,
    )
    invalid = {
        "invalid-secret": "Production settings",  # pragma: allowlist secret - validation error label
        "invalid-service": "Production settings",
        "empty-game-cookie": "game_token_cookie_secure",
        "empty-active-cookie": "active_character_cookie_secure",
        "empty-locations": "authx_jwt_token_locations",
        "invalid-stage": "release_stage",
        "invalid-storage": "asset_storage_backend",
    }
    if mode in invalid:
        assert parsed.returncode != 0
        assert invalid[mode] in parsed.stderr
        return
    assert parsed.returncode == 0, "Actual play app rejected synthetic environment: " + parsed.stderr
    actual = json.loads(parsed.stdout)
    for key, value in values.items():
        name = key.lower()
        if (
            key not in ALLOWLIST
            or name not in actual
            or key in {"DEBUG", "FRONTEND_SURFACE", "DATABASE_URL", "REALTIME_WS_URL"}
        ):
            continue
        target = actual[name]
        if isinstance(target, bool):
            assert target is (value.lower() == "true")
        elif isinstance(target, int):
            assert target == int(value)
        elif isinstance(target, float):
            assert target == float(value)
        elif isinstance(target, list):
            assert target == json.loads(value)
        else:
            assert target == value
    assert actual["database_url"] == values["SITE_DATABASE_URL"]
    assert actual["realtime_ws_url"] == (values.get("REALTIME_WS_URL") or values["PLAY_PUBLIC_BASE_URL"])
    assert (
        actual["smtp_password"] == ""
        and actual["backend_operator_write_key"] == ""
        and actual["backend_operator_read_key"] == ""
    )
    if mode == "defaults":
        assert actual["smtp_host"] == "smtp.gmail.com" and actual["smtp_port"] == 587
        assert actual["smtp_start_tls"] is True
        assert actual["auth_cookie_secure"] is False
        assert actual["auth_user_cache_ttl_seconds"] == 1800
        assert actual["release_stage"] == "alpha"
