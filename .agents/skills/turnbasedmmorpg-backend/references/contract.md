# TurnBasedMMORPG Backend - consumer contract map

Use this route when consuming the domain without changing its internals. This map points to existing guidance; it is not a newly verified API specification. The structural split preserves the previous guidance snapshot. Current signatures, complete DTO schemas, errors and end-to-end examples still require a separate substantive refresh against code/tests. Do not infer availability from a planned or retired surface.

## Read for the consumer task

| Consumer task | Existing contract material | Boundary / detail to check |
| --- | --- | --- |
| Call game APIs or consume feature DTOs | [feature architecture](feature-architecture.md) | API/DTO and integration ownership; inspect the owning router for current signatures and audience. |
| Communicate across features | [event bus](event-bus.md) | Semantic integration calls, thin handlers and request/reply; detailed [Streams contract](redis-streams.md). |
| Read persisted state or heavy documents | [storage ownership](storage-ownership.md) | PostgreSQL/Mongo boundary; see [document patterns](document-patterns.md). |

## Pending contract detail

This skill spans several features rather than a single callable service. A complete inventory of per-feature public routes/events, DTO schemas, authorization requirements, timeout/retry behavior and caller examples has not been assembled here; check each owning surface before use.

## Before integrating

Read the linked material for the affected surface; confirm the owning public entry point, input/output DTOs, rejection or unavailable behavior and an applicable example in current code/tests. If those details are absent, record the gap rather than inventing an API or bypassing the owner. Internal changes follow [properties](properties.md).
