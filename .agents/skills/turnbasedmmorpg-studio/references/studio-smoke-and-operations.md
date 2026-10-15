# Studio smoke tests and operations

## Smoke-test snippet

After any studio change, this should pass:

```powershell
cd <TurnBasedMMORPG repository root>
uv run ruff check src/studio src/frontend
uv run mypy src/studio
```

```python
# Functional check (run via: PYTHONPATH=src uv run python -c "...")
from fastapi.testclient import TestClient
from src.studio.app import app

with TestClient(app) as client:
    assert client.get("/health").status_code == 200

    # Home tiles list all registered modules.
    home = client.get("/")
    assert home.status_code == 200
    assert "Studio" in home.text
    assert "/admin/" in home.text  # at least one tile link

    # Source switcher.
    r = client.post("/studio/source", data={"source": "prod", "next_url": "/"}, follow_redirects=False)
    assert r.status_code == 303
    assert "studio_source=prod" in r.headers.get("set-cookie", "")

    # Switched-state badge.
    home_prod = client.get("/", cookies={"studio_source": "prod"})
    assert "PROD READ-ONLY" in home_prod.text
```

## Diagnosing failures

If a dashboard renders empty or 500s:

```powershell
# 1. Is studio reaching backend at all?
docker exec tbmmorpg-studio sh -c 'curl -sf -o - -w "\nHTTP %{http_code}\n" http://backend:8001/health'

# 2. Is the specific endpoint healthy?
docker exec tbmmorpg-studio sh -c 'curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "X-Internal-Service-Key: dev-site-to-game-service-key" "http://backend:8001/api/<endpoint>"'

# 3. If the endpoint returns 500, the backend logs hold the trace:
docker logs tbmmorpg-backend --tail 200 | grep -E "Traceback|Error|<endpoint-fragment>"
```

In studio's own logs:

- `BackendRequestRejected` (line 72 in `src.frontend.core.api`) means backend
  responded with non-2xx. Usually a backend bug or auth mismatch.
- `BackendRequestUnavailable` (line 75) means studio couldn't connect.
  Usually network/DNS, backend not running, or wrong `api_base` configuration.

## SSH tunnel mode

`SshTunnelManager` runs in `detect` mode today. It probes the configured local
ports and, if any are closed, hints with a copy-paste command. It does **not**
open tunnels itself. The `manage` mode (programmatic open via `sshtunnel` or
`asyncssh`) is intentionally a TODO until a studio module actually needs prod
data — picking the SSH library should match what other project tooling already
uses.

## Future extensions (not yet implemented)

- **`prod_snapshot` source** — a NEON-hosted (or local) Postgres dump of prod,
  selected by the dropdown alongside `local` and `prod`. The intended workflow
  for analytics work; see `../SKILL.md` Read-Only-On-Prod section.
- **Read-only guard middleware** — block non-GET requests in studio when
  `request.state.source.kind in {"prod"}`. Defensive layer on top of the
  contract.
- **Local arq workers** — optional studio-owned workers under
  `src/studio/workers/` for heavy compute that should not even hit a local
  backend. Skipped for now because `combat-ai-simulation-worker` already runs
  on the developer's machine via local `docker-compose.yml`.
