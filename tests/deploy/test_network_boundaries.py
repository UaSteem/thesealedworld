"""Check effective nginx location selection and development port bindings.

These contract checks complement nginx -t; they do not replace its syntax check.
"""

import json
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from posixpath import normpath
from urllib.parse import unquote, urlsplit

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
        "/metrics",
        "/metrics/",
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


@pytest.mark.parametrize(
    "uri",
    [
        "/api/admin",
        "/api//internal/sessions?limit=1",
        "/api/%69nternal/sessions",
        "/api/internal%2fsessions",
        "/api/public/../admin/players",
        "/%64ocs?redirect=/api/characters",
        "//redoc/",
        "/openapi%2ejson",
    ],
)
def test_normalized_internal_paths_cannot_fall_through_to_upstreams(public_servers, uri):
    # Nginx matches locations against decoded, dot-resolved URIs with merge_slashes on.
    path = normpath("/" + unquote(urlsplit("https://example.test" + uri).path).lstrip("/"))
    for server in public_servers:
        assert "merge_slashes off" not in server
        assert "return 404;" in _select_location(server, path)


@pytest.mark.parametrize(
    "filenames,public_services",
    [
        (("docker-compose.yml",), set()),
        (("docker-compose.db.yml",), set()),
        (("docker-compose.yml", "docker-compose.observability.yml"), set()),
        (("compose.prod.yml",), {"nginx"}),
    ],
)
@pytest.mark.external
def test_resolved_compose_publishes_only_intended_interfaces(tmp_path, filenames, public_services):
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("Docker Compose CLI is required for resolved configuration checks")
    # Do not load repository .env or service env files, or print resolved secrets.
    empty_env = tmp_path / "empty.env"
    empty_env.write_text("")
    environment = os.environ.copy()
    for file in (ROOT / "deploy").glob("*.yml"):
        for name in re.findall(r"\$\{([A-Z][A-Z0-9_]*)", file.read_text()):
            environment[name] = "contract-test"
    environment.update(
        DOMAIN_NAME="example.test",
        PLAY_DOMAIN_NAME="play.example.test",
        DEPLOY_ENV_FILE=str(empty_env),
        COMPOSE_PROFILES="",
    )
    command = [docker, "compose", "--env-file", str(empty_env)]
    for filename in filenames:
        command.extend(("-f", str(ROOT / "deploy" / filename)))
    command.extend(("config", "--no-env-resolution", "--format", "json"))
    result = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, "Docker Compose configuration validation failed"
    services = json.loads(result.stdout)["services"]
    published = set()
    for name, service in services.items():
        assert service.get("network_mode") != "host", name
        for port in service.get("ports", []):
            published.add(name)
            if name not in public_services:
                assert port.get("host_ip") == "127.0.0.1", (filenames, name, port)
            else:
                assert (port["target"], str(port["published"]), port.get("protocol", "tcp")) in {
                    (80, "80", "tcp"),
                    (443, "443", "tcp"),
                }, (filenames, name, port)
    if public_services:
        assert published == public_services
    else:
        assert published


@pytest.mark.external
@pytest.mark.skipif(os.environ.get("RUN_NGINX_CONTAINER_TEST") != "1", reason="Opt-in isolated Docker check")
def test_real_nginx_denies_private_routes_on_both_public_hosts(tmp_path):
    """Use only an existing image, no published ports, network or working stack."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.test")])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(hours=1))
        .sign(private_key, hashes.SHA256())
    )
    (tmp_path / "certificate.pem").write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    (tmp_path / "key.pem").write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        )
    )
    template = (ROOT / "deploy/nginx/site.conf.template").read_text()
    replacements = {
        "DOMAIN_NAME": "example.test",
        "PLAY_DOMAIN_NAME": "play.example.test",
        "TLS_CERTIFICATE_PATH": "/contract/certificate.pem",
        "TLS_CERTIFICATE_KEY_PATH": "/contract/key.pem",
        "PLAY_TLS_CERTIFICATE_PATH": "/contract/certificate.pem",
        "PLAY_TLS_CERTIFICATE_KEY_PATH": "/contract/key.pem",
    }
    for variable, value in replacements.items():
        template = template.replace("${" + variable + "}", value)
    # Dummy upstream responds 200 to every path: a leaked private request fails the test.
    template = re.sub(r"http://(?:frontend(?:-play)?|backend|chat):\d+", "http://127.0.0.1:18081", template)
    template += "\nserver { listen 127.0.0.1:18081; return 200 'public upstream'; }\n"
    (tmp_path / "site.conf").write_text(template)
    main = (ROOT / "deploy/nginx/nginx.conf").read_text()
    (tmp_path / "nginx.conf").write_text(
        main.replace("include /etc/nginx/conf.d/*.conf;", "include /contract/site.conf;")
    )
    script = """
set -eu
nginx -t -c /contract/nginx.conf
nginx -c /contract/nginx.conf
trap 'nginx -s quit -c /contract/nginx.conf' EXIT
for host in example.test play.example.test; do
    for path in /api/internal /api/internal/sessions /api/admin /api/admin/players \
        /api//internal/sessions /api/%69nternal/sessions /api/internal%2fsessions \
        /api/public/../admin/players /docs /docs/oauth2-redirect /%64ocs /redoc/ /openapi%2ejson \
        /metrics /metrics/ /%6detrics; do
        code=$(curl --silent --show-error --path-as-is --insecure --max-time 5 \
            -H "Host: $host" -o /dev/null -w '%{http_code}' "https://127.0.0.1$path")
        [ "$code" = 404 ] || { echo "Unexpected $code for $host $path"; exit 1; }
    done
    for path in /admin/players /api/characters /api/internalized /chat/history; do
        code=$(curl --silent --show-error --insecure --max-time 5 \
            -H "Host: $host" -o /dev/null -w '%{http_code}' "https://127.0.0.1$path")
        [ "$code" = 200 ] || { echo "Unexpected $code for $host $path"; exit 1; }
    done
done
"""
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--pull",
            "never",
            "--network",
            "none",
            "--mount",
            f"type=bind,source={tmp_path.resolve()},target=/contract,readonly",
            "--entrypoint",
            "sh",
            os.environ.get("NGINX_TEST_IMAGE", "deploy-nginx:latest"),
            "-c",
            script,
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
