# TurnBasedMMORPG Feature Slice

## Read by task

A cross-feature slice uses .agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md. Read .agents/skills/turnbasedmmorpg-frontend/references/feature-architecture.md when the slice changes routes, templates, view models, or API clients. Read .agents/skills/turnbasedmmorpg-backend/references/event-bus.md when events or workers are involved, and .agents/skills/turnbasedmmorpg-project/references/project-rules.md when ownership or shared contracts change. Before completion, choose checks via .agents/skills/turnbasedmmorpg-quality/references/validation.md.
## Slice Order

1. Identify the owning backend feature.
2. Define backend API request/response contracts.
3. Put shared contracts in `src/shared` only if frontend and backend both use them.
4. Implement backend integrations before services when the feature needs infrastructure, Redis Streams, session managers, repositories, or cross-feature flows.
5. Put Redis/cache/session managers under `src/backend/infrastructure/<domain>/managers/` when the slice owns keys, RedisJSON paths, TTLs, locks, Lua scripts, scan patterns, or delete/touch behavior. One key-space has one manager.
6. Implement backend service/repository/runtime changes inside the owning feature. Services/runtime code should call semantic integration methods for infrastructure work.
7. Add or update the frontend backend API client.
8. Add frontend routes, services, view models, forms, and templates inside the owning frontend feature.
9. Add Redis Streams events only for cross-feature backend communication. Handlers stay thin; see .agents/skills/turnbasedmmorpg-backend/references/event-bus.md for ownership and examples.
10. Add focused tests for the changed backend, shared contracts, and frontend integration points.
11. Run the strongest practical quality gate through `tools/dev/check.py` or documented targeted fallback checks.

## Keep Boundaries

Do not skip the backend API client by importing backend services from frontend.

Do not move feature-specific behavior into global core modules.

Do not create shared DTOs for one-side-only convenience.

Do not wire feature services directly to low-level `src/backend/infrastructure/<domain>/` modules when an integration boundary is part of the feature slice.

Do not build Redis keys, RedisJSON paths, TTLs, locks, Lua scripts, or scan patterns inside feature services, repositories, events, or workers. Add methods to the owning infrastructure manager and call those methods directly only from dependency wiring or purely technical workers; otherwise expose semantic feature operations through `integrations/`.
