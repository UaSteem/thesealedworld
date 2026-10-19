# Project Rules

## Source Tree

Use `src/` as the target application tree:

```text
src/
  backend/
  frontend/
  shared/
```

Use `temp/` only as donor code. It may contain useful algorithms, resource data, old services, and old DTO ideas, but its layout is not the target architecture.

## Ownership

Backend features own game behavior, persistence, runtime state, events, and workers. Backend directly owns the game database (`tbmmorpg_game`), Redis game state, and Mongo game collections (`tbmmorpg_analytics`).

Backend feature `integrations/` modules are the expected boundary between feature logic and backend infrastructure. When feature code needs repositories, managers, schemas, sessions, Redis Streams clients, or cross-feature flows, add or update a semantic integration instead of wiring services directly to infrastructure.

Backend infrastructure is domain-grouped under `src/backend/infrastructure/<domain>/` and may contain low-level `schemas/`, `models/`, `repositories/`, `managers/`, and adapters for that domain.

Redis key-space ownership belongs to backend infrastructure managers. A feature service, repository, event handler, or worker must not construct Redis keys, RedisJSON paths, TTL behavior, lock keys, Lua scripts, scan patterns, or delete/touch behavior directly. One Redis key-space has one owning manager, and that manager exposes methods for stable nested RedisJSON sections when callers need to work below the top-level document.

Frontend features own browser routes, page/fragment orchestration, forms, view models, and templates. Frontend directly owns the site database (`tbmmorpg_site`: accounts, auth, news, surveys, site Alembic migrations).

Shared code owns cross-service enums, DTO contracts, and shared infrastructure helpers (`logging_config`, `log_middleware`, `metrics_middleware`). It must not contain domain business logic, ORM models, or service state.

## Boundaries

Do not import `src.backend.features` from frontend code.

Frontend must never directly access the game database (`tbmmorpg_game`), Redis game state (`game:*`, `combat:*`), or Mongo game collections (`tbmmorpg_analytics`). All game interactions must go through Backend HTTP/WS APIs.

Do not put frontend view models in shared code.

Do not put backend-internal service DTOs, ORM models, or domain business logic in shared code.

Do not create global repositories or global Redis managers that know every game domain.

Do not put Redis managers inside `src/backend/features/<feature>/services/` or `src/backend/features/<feature>/repositories/`. Use `src/backend/infrastructure/<domain>/managers/` and wrap it from feature `integrations/` when feature logic needs a semantic boundary.

Do not recreate a central dispatcher that replaces feature ownership.

Do not skip a feature integration layer for new infrastructure access just because the feature is still incomplete. Missing feature folders mean the slice has not been built yet, not that services should bypass the intended boundary.

## Donor Code Migration

When migrating from `temp/`:

1. Identify the behavior or data being kept.
2. Place it inside the owning `src/backend/features/<feature>` or `src/frontend/features/<feature>`.
3. Rename files and classes to match the current feature vocabulary.
4. Replace direct cross-feature calls with API contracts or Redis Streams events.
5. Add or update focused tests for the migrated behavior.

## Shared Contracts

Use `src/shared` only for models, enums, DTOs, and shared infrastructure helpers used by both sides at an explicit boundary.

Good candidates:

- backend API request models used by frontend clients
- backend API response models parsed by frontend clients
- stable enums used by those API contracts
- shared infrastructure helpers used by both backend and frontend (`logging_config`, `log_middleware`, `metrics_middleware`)

Bad candidates:

- frontend template view models
- backend repository models, ORM models, or service state
- domain business logic or game rule calculations
- Redis runtime internals not exposed by API, including `game:ac:<char_id>` active character sessions and `game:actor:snapshot:*` temporary actor projections
- temporary helper schemas used only on one side

## Runtime State Terms

Use these terms consistently:

- Active character session: `game:ac:<char_id>`, the live Redis document for a selected character. It holds current runtime state such as vitals, location, game state, symbiote, attributes, skills, and active feature refs.
- Actor snapshot/projection: `game:actor:snapshot:*`, a temporary on-demand context built for a combat scope. It is derived data and can expire.
- Character combat snapshot: a character-owned projection built by `character.combat_snapshots_requested` from `game:ac:<char_id>` plus monster runtime sources.

## Stage Demarcation and Generation Determinism (SG10-K1, SG10-W4)

- **Legacy**: Old node-based Rift (`src/backend/features/rift/`). Do not refactor or change player contracts without explicit owner approval.
- **Experimental / Dev-only**: Hex Rift (`tests/backend/features/rift/test_hex_rift.py`, `/api/dev/rift`). Must stay gated by `enable_dev_rift_routes` and blocked at public edge.
- **Pre-alpha Active Target**: World, Expedition, and Exploration feature slices.
- **Generation Determinism**: All procedural generation and simulations must use isolated `random.Random(seed)` instances. Never invoke global `random.seed()`. Stabilize unordered candidates before RNG selection to prevent `PYTHONHASHSEED` nondeterminism across processes; preserve explicitly authored or priority-sensitive sequence order.
