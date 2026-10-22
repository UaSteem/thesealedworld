"""Database-only site migration settings do not bypass HTTP authentication."""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("valid_auth", [False, True])
def test_site_database_import_preserves_frontend_auth_validation(tmp_path, valid_auth):
    environment = os.environ.copy()
    for source in (ROOT / "src/frontend/config").glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                environment.pop(node.target.id.upper(), None)
    environment.update(
        PYTHONPATH=str(ROOT),
        DEBUG="False",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SITE_DATABASE_URL="sqlite+aiosqlite:///:memory:",
        VALID_AUTH=str(valid_auth),
    )
    if valid_auth:
        environment.update(
            SECRET_KEY="synthetic-production-signing-key",  # pragma: allowlist secret
            BACKEND_INTERNAL_SERVICE_KEY="synthetic-service-key",  # pragma: allowlist secret - synthetic fixture
        )  # pragma: allowlist secret
    script = r"""
import os, socket, sys, pydantic_settings
original = pydantic_settings.SettingsConfigDict
def without_dotenv(*a, **k):
    k['env_file'] = None
    return original(*a, **k)
pydantic_settings.SettingsConfigDict = without_dotenv
def forbidden(*a, **k): raise AssertionError('No network')
socket.socket.connect = forbidden
socket.socket.connect_ex = forbidden
socket.create_connection = forbidden
from src.frontend.config.database import DatabaseSettings, database_settings
from src.frontend.core.database import load_orm_models, async_engine
load_orm_models()
assert 'src.frontend.config.settings' not in sys.modules
assert not {'secret_key','backend_internal_service_key','smtp_password'} & DatabaseSettings.model_fields.keys()
assert async_engine.url.database == ':memory:'
if os.environ['VALID_AUTH'] == 'True':
    from src.frontend.config.settings import settings
    for name in DatabaseSettings.model_fields:
        assert getattr(settings, name) == getattr(database_settings, name)
else:
    try:
        import src.frontend.config.settings
    except ValueError as exc:
        assert 'Production settings cannot use default or development secret keys' in str(exc)
    else:
        raise AssertionError('Frontend auth validation was bypassed')
"""
    result = subprocess.run(
        [sys.executable, "-c", script], env=environment, cwd=tmp_path, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
