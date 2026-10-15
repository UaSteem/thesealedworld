## Source Switcher Contract

`SourceSelectorMiddleware` (`src/studio/features/source_selector/middleware.py`)
attaches a `Source` to every request at `request.state.source`. Resolution
order:

1. Cookie `studio_source` (set by the header dropdown).
2. Fallback: `STUDIO_SOURCE` env var.
3. Default: `local`.

Each `Source` (defined in `src/studio/settings.py`) carries:

- `kind` — `"local"` | `"prod"` (and later `"prod_snapshot"`).
- `api_base` — backend HTTP base URL used by studio cabinet modules.
- `pg_dsn` / `redis_url` — when a future module needs direct DB/Redis reads.
- `ssh_host` / `ssh_forwards` — when the source requires an SSH tunnel.

Backend API clients **must** read the base URL from
`request.state.source.api_base`, not from `frontend.config.settings`:

```python
api = SomeBackendApi(client=client, base_url=request.state.source.api_base)
```

This makes every cabinet module source-aware automatically — switching the
header dropdown changes which backend the module queries on the next request.

## Backend Connectivity

Studio talks to a backend through HTTP. It does **not** import backend
internals, and it does **not** open its own Postgres/Redis pools yet (the
registries exist in `features/sources/` for future use, but no module uses
them today).

- For local source, the backend service in `deploy/docker-compose.yml`
  resolves as `http://backend:8001` (set via `LOCAL_API_BASE` env var).
- For prod source, the API base is `http://host.docker.internal:18001` and
  the developer opens an SSH tunnel manually:

  ```powershell
  ssh -N -L 15432:127.0.0.1:5432 -L 16379:127.0.0.1:6379 -L 18001:127.0.0.1:8001 my_game
  ```

  The `my_game` SSH host alias is the same one `deploy/README.md` documents
  for the project's admin tools (CloudBeaver, RedisInsight).

Studio reuses two pieces from `src/frontend`:

- `src.frontend.core.api.BaseApiClient` — the shared HTTP client base.
- `src.frontend.integrations.backend_api.<client>` — any client that is also
  used by a module still in the prod cabinet (`combat_sessions`,
  `exploration_sessions`, `scenario_sessions`, `game_config`,
  `combat_ai_testing`). These stay in frontend because they have a second
  consumer there; studio imports them by their existing path.

Clients used **only** by studio modules live under
`src/studio/integrations/backend_api/` (currently: `admin_monsters.py`,
`combat_analytics.py`).

## Adding A New Module

Apply the same pattern as the existing five migrated modules:

1. Create `src/studio/features/cabinet/modules/<m>/` with `__init__.py` and
   `cabinet.py`. Add a `CabinetAdmin` subclass that registers itself via
   `cabinet_site.register(<m>Admin)` at import time.
2. Set `group_label` to a stable Russian phrase so the home-page tiles and
   sidebar group consistently (`Контент`, `Гейм Сервер`, `Аналитика`, etc.).
3. Add the dotted import path to `src/studio/cabinet.py::CABINET_MODULES`.
4. For data the module needs:
   - If the backend already exposes an endpoint, add a typed HTTP client.
     Place it in `src/studio/integrations/backend_api/<client>.py` if only
     studio uses it, or in `src/frontend/integrations/backend_api/` if a prod
     module also uses it.
   - Always pass `base_url=request.state.source.api_base`.
   - Catch `httpx.HTTPStatusError` / `httpx.RequestError` in providers and
     return empty widgets rather than 500ing the dashboard — backend WIP and
     intermittent unavailability must not break the studio shell.
5. If the module needs to render anything other than the default cabinet
   widgets, the template must live in `src/fastapi_cabinet/templates/cabinet/`
   (the library owns the cabinet templates; both frontend and studio share
   them).
6. Run `uv run ruff check src/studio src/frontend && uv run mypy src/studio`
   before committing.
