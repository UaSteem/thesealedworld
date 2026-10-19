# TurnBasedMMORPG Studio

## Read by task

For studio source selection and module wiring, read .agents/skills/turnbasedmmorpg-studio/references/source-switcher-modules.md and the relevant part of .agents/skills/turnbasedmmorpg-studio/references/studio-architecture.md. Read .agents/skills/turnbasedmmorpg-frontend/references/feature-architecture.md only for shared frontend boundaries, and .agents/skills/turnbasedmmorpg-frontend/references/cabinet-design.md for cabinet UI changes. Backend API contracts use .agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md.
## What Studio Is

Studio is a **second frontend application** under `src/studio/`, structurally
mirroring `src/frontend/` (own `app.py`, `cabinet.py`, `features/`, `templates/`,
`static/`, `integrations/`). It hosts the **analytical cabinet** — heavy data
exploration views and historical aggregates that have no place on the prod
admin surface.

- Runs on **port 9100**, locally only.
- **Never deployed to prod.** `deploy/compose.site.yml`, `compose.game.yml`,
  `compose.infra.yml`, `compose.tg-bot.yml` do not reference studio.
  `deploy/frontend/Dockerfile` and `deploy/backend/Dockerfile` use whitelisted
  `COPY src/<dir>` and never copy `src/studio/`.
- Lives in the local dev stack only via the `studio` service in
  `deploy/docker-compose.yml`.

## Why It Exists

The prod admin cabinet (`src/frontend/features/cabinet/`) used to host both
live-ops and analytical modules. Analytical modules:

- triggered heavy `GROUP BY` queries on prod Postgres on every page open;
- enlarged the prod attack surface (more endpoints behind the admin gate);
- slowed iteration — any dashboard change required a prod release.

Studio extracts the analytical modules into a separate frontend so that:

1. Prod cabinet stays slim and live-ops-focused.
2. Heavy reads happen against a developer-controlled data source (local DB
   or a snapshot of prod), not against live prod.
3. Studio can be iterated freely without touching prod.

## What Stays In Prod vs What Goes To Studio

Decide by **load and intent**, not by feature area:

| Prod cabinet (live-ops, light) | Studio (analytical, heavy) |
|---|---|
| Live-publishing (`news_management`) | History of sessions over time |
| Moderation / bans (`accounts`) | Multi-day rollups, drilldowns |
| Live config writes / kill-switches (`game_settings`) | AI simulations |
| Light realtime metrics (`game_server`, `site_analytics`, `player_analytics`) | Large content scans (monsters + omens) |
| Live user comms (`messaging`, `feedback`) | Reports built from historical fact tables |

Rule of thumb:

- **Prod cabinet** answers "what do I do with the system right now."
- **Studio** answers "what do I want to learn from the data."

Current split is committed:

- Prod `CABINET_MODULES` (`src/frontend/cabinet.py`): `news_management`,
  `site_analytics`, `site_ops`, `player_analytics`, `accounts`, `game_server`,
  `game_settings`, `messaging`, `feedback`.
- Studio `CABINET_MODULES` (`src/studio/cabinet.py`): `content_ops`,
  `scenario`, `exploration`, `combat`, `combat_ai_testing`.

## Read-Only Source vs Local Compute Boundary (SG10-K4)

Studio must **never mutate the selected data source** (`LOCAL` or `PROD`). When connected to any data source, it must not:

- POST to endpoints that mutate the selected source (no triggering image regeneration, AI updates, monster rebuilds against the source);
- write to Postgres or Redis of the selected source;
- enqueue arq jobs on the selected source's queues.

Local analytical compute or explicitly triggered local dev simulation jobs are permitted **only when the effective selected source is local (`request.state.source.kind`; the source cookie takes precedence over the `STUDIO_SOURCE` fallback)** and must be strictly blocked when inspecting a read-only or remote source. The prod `combat-ai-simulation-worker` in `deploy/compose.game.yml` is gated by the `combat-ai-simulation` profile and is not part of the default prod composition.

The future intended workflow for prod data is:

1. A NEON (or pg_dump) **snapshot** of prod Postgres lives as a third source
   alongside `local` and `prod`.
2. Studio's Source Switcher selects between `local`, `prod` (live read-only
   via SSH), and the snapshot.
3. Heavy exploration runs against the snapshot, not against live prod.

Until the snapshot source is in place, treat the live `prod` source as
**hands-off** outside of read paths.
