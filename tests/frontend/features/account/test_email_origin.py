"""Canonical email origins do not trust request Host or forwarded headers."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]


def _isolated(tmp_path, script):
    env = os.environ.copy()
    # Never read application dotenv files or inherit deployment settings.
    for key in list(env):
        if key not in {
            "PATH",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "COMSPEC",
            "PATHEXT",
            "USERPROFILE",
            "APPDATA",
            "LOCALAPPDATA",
        }:
            env.pop(key, None)
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / "src")])
    prefix = """
import pydantic_settings, socket
original = pydantic_settings.SettingsConfigDict
def without_dotenv(*args, **kwargs):
    kwargs['env_file'] = None
    return original(*args, **kwargs)
pydantic_settings.SettingsConfigDict = without_dotenv
def forbid_connection(*args, **kwargs):
    raise AssertionError('Network access forbidden in email origin contract')
socket.socket.connect = forbid_connection
socket.socket.connect_ex = forbid_connection
socket.create_connection = forbid_connection
"""
    result = subprocess.run(
        [sys.executable, "-c", prefix + script], env=env, cwd=tmp_path, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_email_builder_uses_canonical_origin_despite_request_headers(tmp_path):
    actual = _isolated(
        tmp_path,
        """
import json
from types import SimpleNamespace
from starlette.requests import Request
from src.frontend.features.account.routes import email_verify as routes
from src.frontend.config.settings import settings
settings.debug = False
settings.site_base_url = 'https://accounts.example.test'
routes.get_email_service = lambda: SimpleNamespace()
routes.UserRepository = lambda **kwargs: SimpleNamespace()
routes.TokenRepository = lambda **kwargs: SimpleNamespace()
routes.EmailVerificationService = lambda **kwargs: SimpleNamespace(**kwargs)
scope = dict(type='http', scheme='http', path='/account/security/email/verify', root_path='', query_string=b'', server=('internal', 8000), client=('198.51.100.9', 1234), headers=[(b'host', b'hostile.example.test'), (b'x-forwarded-proto', b'http'), (b'x-forwarded-host', b'hostile.example.test'), (b'forwarded', b'host=hostile.example.test;proto=http')])
service = routes._build_service(Request(scope), object())
print(json.dumps({'origin': service._site_base_url if hasattr(service, '_site_base_url') else service.site_base_url}))
""",
    )
    assert actual == {"origin": "https://accounts.example.test"}


@pytest.mark.parametrize(
    "origin",
    [
        "",
        "http://accounts.example.test",
        "https://user:password@accounts.example.test",  # pragma: allowlist secret - invalid synthetic URL fixture
        "https://accounts.example.test/path",
        "https://accounts.example.test?x=1",
        "https://accounts.example.test#fragment",
        "//accounts.example.test",
        "https://accounts.example.test\\evil",
        "https://accounts.example.test\n",
        "https://accounts.example.test:99999",
    ],
)
def test_invalid_email_origins_are_rejected(origin):
    from src.frontend.features.email.origin import canonical_email_origin

    with pytest.raises(ValueError):
        canonical_email_origin(origin)


@pytest.mark.parametrize(
    "origin,expected",
    [
        ("https://accounts.example.test/", "https://accounts.example.test"),
        ("https://accounts.example.test:8443", "https://accounts.example.test:8443"),
    ],
)
def test_https_email_origin_is_normalized(origin, expected):
    from src.frontend.features.email.origin import canonical_email_origin

    assert canonical_email_origin(origin) == expected


def test_development_fallback_is_stable_and_only_loopback_allows_http():
    from src.frontend.features.email.origin import canonical_email_origin

    assert canonical_email_origin("", allow_local_http=True) == "http://localhost:8000"
    assert canonical_email_origin("http://localhost:8080/", allow_local_http=True) == "http://localhost:8080"
    assert canonical_email_origin("http://[::1]:8080", allow_local_http=True) == "http://[::1]:8080"
    assert (
        canonical_email_origin("http://thesealed.localhost:8080", allow_local_http=True)
        == "http://thesealed.localhost:8080"
    )
    with pytest.raises(ValueError):
        canonical_email_origin("http://hostile.example.test", allow_local_http=True)


def test_email_settings_require_https_canonical_origin_only_when_enabled(tmp_path):
    actual = _isolated(
        tmp_path,
        """
import json
from pydantic import ValidationError
from src.frontend.config.settings import FrontendSettings
kwargs = dict(_env_file=None, debug=False, secret_key='synthetic-production-key', backend_internal_service_key='synthetic-service-key') # pragma: allowlist secret - synthetic fixtures
settings = FrontendSettings(**kwargs, enable_email_verification=False)
assert settings.site_base_url == ''
rejected = []
for origin in ['', 'http://accounts.example.test', 'https://accounts.example.test/path']:
    try:
        FrontendSettings(**kwargs, enable_email_verification=True, site_base_url=origin)
    except ValidationError:
        rejected.append(origin)
    else:
        raise AssertionError('Unsafe canonical origin accepted')
valid = FrontendSettings(**kwargs, enable_email_verification=True, site_base_url='https://accounts.example.test/')
assert valid.site_base_url == 'https://accounts.example.test/'
print(json.dumps({'rejected': len(rejected)}))
""",
    )
    assert actual == {"rejected": 3}


def test_bounded_proxy_trust_does_not_control_email_origin(tmp_path):
    actual = _isolated(
        tmp_path,
        """
import asyncio, json
from types import SimpleNamespace
from starlette.requests import Request
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from src.frontend.features.account.routes import email_verify as routes
from src.frontend.config.settings import settings
settings.debug = False
settings.site_base_url = 'https://accounts.example.test/'
routes.get_email_service = lambda: SimpleNamespace()
routes.UserRepository = lambda **kwargs: SimpleNamespace()
routes.TokenRepository = lambda **kwargs: SimpleNamespace()
routes.EmailVerificationService = lambda **kwargs: SimpleNamespace(**kwargs)
results = []
async def app(scope, receive, send):
    service = routes._build_service(Request(scope), object())
    results.append(dict(origin=service.site_base_url, scheme=scope['scheme'], client=scope['client'][0]))
proxy = ProxyHeadersMiddleware(app, trusted_hosts=['10.22.33.4'])
async def run():
    for peer in ['10.22.33.4', '198.51.100.9']:
        scope = dict(type='http', scheme='http', path='/', root_path='', query_string=b'', server=('internal',8000), client=(peer,1234), headers=[(b'host',b'hostile.example.test'),(b'x-forwarded-proto',b'https'),(b'x-forwarded-for',b'203.0.113.77'),(b'x-forwarded-host',b'hostile.example.test')])
        async def receive(): return dict(type='http.request',body=b'',more_body=False)
        async def send(message): pass
        await proxy(scope, receive, send)
coroutine = run()
try:
    coroutine.send(None)
except StopIteration:
    pass
else:
    coroutine.close()
    raise AssertionError('Proxy-only ASGI contract must not await external I/O')
print(json.dumps(results))
""",
    )
    assert actual == [
        {"origin": "https://accounts.example.test", "scheme": "https", "client": "203.0.113.77"},
        {"origin": "https://accounts.example.test", "scheme": "http", "client": "198.51.100.9"},
    ]


def test_verification_service_rejects_unsafe_origin_before_token_issue():
    from unittest.mock import MagicMock

    from src.frontend.features.account.services.email_verification_service import EmailVerificationService

    session = MagicMock()
    with pytest.raises(ValueError):
        EmailVerificationService(
            session, MagicMock(), MagicMock(), MagicMock(), site_base_url="http://hostile.example.test"
        )
    session.add.assert_not_called()
    session.commit.assert_not_called()
