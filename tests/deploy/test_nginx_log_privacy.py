"""Exercise the production logging format using an isolated, offline Nginx."""

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CANARY = "synthetic-private-url-canary"


@pytest.mark.external
@pytest.mark.skipif(os.getenv("RUN_NGINX_CONTAINER_TEST") != "1", reason="Opt-in isolated Docker check")
def test_access_and_request_errors_do_not_retain_url_secrets(tmp_path):
    main = (ROOT / "deploy/nginx/nginx.conf").read_text()
    main = main.replace("/var/log/nginx/access.log", "/tmp/access.json")
    main = main.replace("/var/log/nginx/error.log", "/tmp/master-error.log")
    main = main.replace("include /etc/nginx/conf.d/*.conf;", "include /contract/site.conf;")
    (tmp_path / "nginx.conf").write_text(main)
    (tmp_path / "site.conf").write_text(
        "server { listen 127.0.0.1:18080; "
        "location /broken/ { proxy_pass http://127.0.0.1:9; } "
        "location / { return 200 'ok'; } }"
    )
    paths = [
        f"/surveys/{CANARY}?token={CANARY}",
        f"/account/email/verify?token={CANARY}",
        f"/ws/chat?token={CANARY}",
        f"/unknown/{CANARY}?email={CANARY}@example.test",
        f"/broken/{CANARY}?token={CANARY}",
    ]
    requests = "\n".join(f"curl --silent --max-time 5 -o /dev/null 'http://127.0.0.1:18080{path}'" for path in paths)
    script = (
        "set -eu\nnginx -t -c /contract/nginx.conf\nnginx -c /contract/nginx.conf\n"
        "trap 'nginx -s quit -c /contract/nginx.conf' EXIT\n"
        + requests
        + "\ncat /tmp/access.json\ncat /tmp/master-error.log\n"
    )
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
            os.getenv("NGINX_TEST_IMAGE", "deploy-nginx:latest"),
            "-c",
            script,
        ],
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert CANARY not in result.stdout + result.stderr
    records = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    assert len(records) == len(paths)
    assert [record["status"] for record in records] == [200, 200, 200, 200, 502]
    assert all(record["method"] == "GET" for record in records)
    assert all(len(record["request_id"]) == 32 for record in records)
    assert all("request_time" in record and "upstream_time" in record for record in records)
    assert all("remote_addr" not in record for record in records)
