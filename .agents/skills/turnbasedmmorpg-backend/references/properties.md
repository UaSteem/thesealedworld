# TurnBasedMMORPG Backend

Backend features own game behavior; feature integrations mediate access to infrastructure. Infrastructure managers own Redis key spaces.
PostgreSQL is the source of truth for relational state; MongoDB stores large flexible documents where the storage contract calls for them.
Use the event bus for cross-feature work. Keep handlers thin and route work through feature-owned services.

## Multi-step Lifecycle Checklist (SG10-W1)

Use these design checks for the affected multi-step operation (rewards, combat finalization, state sync, generation, archive). They are requirements for new work, not a claim that every existing flow already implements them:
1. **Idempotency Key / Duplicate Delivery Guard**: Validate operation/transaction identity before execution to prevent double-processing.
2. **Explicit Commit Point**: Define the authoritative transaction and publish/enqueue only after a successful durable commit, or use the owning transactional outbox contract. Do not assume cross-store atomicity.
3. **External / Mongo Failure Handling**: Wrap external side effects (e.g., MongoDB battle logs, provider calls) with retry status; never advance consumption cursors past failed unpersisted payloads.
4. **Lease / Lock Fencing**: Validate held lock fencing tokens or document generation numbers before final writes to reject stale workers.

## Route Audience Matrix (SG10-W2)

Classify HTTP/WS routes by audience when adding or reviewing them, then enforce the matching authentication/authorization. These are design categories, not an assertion that a common audience decorator exists on every route:
- `public`: Unauthenticated endpoints (e.g., landing, health check).
- `site-auth`: Authenticated site account user (`current_user`).
- `game-session-owner`: Verified character ownership (`current_user.id == character.user_id`) plus an active game session.
- `internal-service`: Inter-service calls gated by `require_internal_service_key`.
- `dev-only`: Gated by configuration setting flags (e.g., `enable_dev_rift_routes`) and blocked at the public Nginx edge proxy.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| New or restructured server catalog, bootstrap or visual-reference registry | [Project catalog conventions](../../turnbasedmmorpg-project/references/catalog-conventions.md) |
| Feature architecture, APIs, repositories | [../references/feature-architecture.md](../references/feature-architecture.md) |
| End-to-end feature slice | [../references/feature-slices.md](../references/feature-slices.md) |
| Redis Streams, publish/request/reply | [../references/event-bus.md](../references/event-bus.md) |
| PostgreSQL/MongoDB ownership | [../references/storage-ownership.md](../references/storage-ownership.md) |
| Large documents, chat, analytics, write flows | [../references/document-patterns.md](../references/document-patterns.md) |
| Source layout or event details | [../references/backend-layout.md](../references/backend-layout.md) |
| Detailed Streams contract | [../references/redis-streams.md](../references/redis-streams.md) |

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
