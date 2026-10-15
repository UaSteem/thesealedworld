## What Studio Must Not Do

- Must not import from `src.backend.*` directly (always go through HTTP API,
  even for read-only data).
- Must not write to any source. Even for `local`, treat the source as
  read-only by convention; the studio is for analysis, not data entry.
- Must not couple cabinet modules to a specific source kind. A module must
  work against `local`, `prod`, and future `prod_snapshot` interchangeably
  via `request.state.source.api_base`.
- Must not be added to any `deploy/compose.*.yml` other than the local
  dev `docker-compose.yml`.
- Must not register routes that mutate prod state when the active source is
  `prod`. (When the read-only guard middleware lands, this will be enforced
  in code; until then it's a contract the module authors must respect.)

## Running Locally

Studio comes up automatically with the rest of the local dev stack:

```powershell
docker compose -f deploy/docker-compose.yml up -d --build
```

- Studio: <http://127.0.0.1:9100>
- Prod cabinet: <http://127.0.0.1:8000/admin>

For fast iteration without docker:

```powershell
uv run uvicorn src.studio.app:app --host 127.0.0.1 --port 9100 --reload
```

The local studio container has `--reload` and host-mounted source volumes, so
Python changes to `src/studio`, `src/frontend`, `src/fastapi_cabinet`, and
`src/shared` reload without rebuild.

## Diagnosing Backend-Side Failures

If a studio dashboard renders empty or 500s, check whether the backend
endpoint itself is broken before assuming studio is at fault:

```powershell
docker exec tbmmorpg-studio sh -c 'curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "X-Internal-Service-Key: dev-site-to-game-service-key" "http://backend:8001/<endpoint>"'
```

`BackendRequestRejected` in studio logs means the backend returned non-2xx.
`BackendRequestUnavailable` means studio couldn't connect at all. The first
is usually a backend bug (e.g. a renamed column an analytics repository still
references). The second is usually network/DNS or backend not running.

## Quality Gate

When changing studio code:

- `uv run ruff check src/studio src/frontend` must pass.
- `uv run mypy src/studio` must pass.
- For the running smoke pattern, see the test snippet in
  `.agents/skills/turnbasedmmorpg-studio/references/studio-smoke-and-operations.md`.

Also apply `.agents/skills/turnbasedmmorpg-quality/references/validation.md` before declaring done, the same way
frontend changes do.

## Stable Documentation Rule

When studio ownership, source-switcher contract, or read-only-on-prod policy
changes, update this skill and the references page. Historical migration plans are not stable documentation.
