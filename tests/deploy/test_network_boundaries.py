"""Check effective nginx location selection and development port bindings.

These contract checks complement nginx -t; they do not replace its syntax check.
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def _blocks(text, expression):
    for match in re.finditer(expression, text):
        depth, end = 1, match.end()
        while depth:
            depth += (text[end] == "{") - (text[end] == "}")
            end += 1
        yield match, text[match.end() : end - 1]


def _select_location(server, path):
    locations = [
        (match.group(1) or "", match.group(2), body)
        for match, body in _blocks(server, r"location\s+(?:(=|\^~|~\*|~)\s+)?(\S+)\s*\{")
    ]
    exact = [body for kind, pattern, body in locations if kind == "=" and pattern == path]
    if exact:
        return exact[0]
    prefixes = [
        (pattern, kind, body) for kind, pattern, body in locations if kind in ("", "^~") and path.startswith(pattern)
    ]
    _, kind, selected = max(prefixes, key=lambda item: len(item[0]))
    if kind != "^~":
        for kind, pattern, body in locations:
            if kind in ("~", "~*") and re.search(pattern, path, re.I if kind == "~*" else 0):
                return body
    return selected


@pytest.fixture
def public_servers():
    text = (ROOT / "deploy/nginx/site.conf.template").read_text()
    result = [body for _, body in _blocks(text, r"server\s*\{") if "set $backend_upstream" in body]
    assert len(result) == 2
    return result


@pytest.mark.parametrize(
    "path",
    [
        "/api/internal",
        "/api/internal/combat/sessions",
        "/api/admin/players",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc/",
        "/openapi.json",
    ],
)
def test_internal_and_schema_paths_denied_on_both_hosts(public_servers, path):
    for server in public_servers:
        assert "return 404;" in _select_location(server, path)


@pytest.mark.parametrize(
    "path,upstream",
    [
        ("/admin/players", "frontend"),
        ("/api/characters", "backend"),
        ("/api/internalized", "backend"),
        ("/ws/realtime", "chat"),
        ("/ws/chat", "chat"),
        ("/chat/history", "chat"),
    ],
)
def test_public_game_admin_ui_and_websockets_preserved(public_servers, path, upstream):
    for server in public_servers:
        body = _select_location(server, path)
        allowed = ("$frontend_upstream", "$play_upstream") if upstream == "frontend" else (f"${upstream}_upstream",)
        assert any(f"proxy_pass {name}" in body for name in allowed)
        if path.startswith("/ws/"):
            assert "proxy_set_header Upgrade $http_upgrade;" in body


@pytest.mark.parametrize(
    "filename", ["docker-compose.yml", "docker-compose.db.yml", "docker-compose.observability.yml"]
)
def test_local_service_ports_bind_loopback(filename):
    data = yaml.safe_load((ROOT / "deploy" / filename).read_text())
    checked = 0
    for name, service in data["services"].items():
        if name == "nginx":
            continue
        for port in service.get("ports", []):
            assert str(port).startswith("127.0.0.1:"), (filename, name)
            checked += 1
    assert checked
