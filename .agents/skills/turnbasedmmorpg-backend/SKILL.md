---
name: turnbasedmmorpg-backend
description: Backend feature ownership, persistence, Redis Streams, and cross-feature slices in TurnBasedMMORPG. Use for backend APIs, services, repositories, workers, or events.
---

# TurnBasedMMORPG Backend

Backend features own game behavior; feature integrations mediate access to infrastructure. Infrastructure managers own Redis key spaces.
PostgreSQL is the source of truth for relational state; MongoDB stores large flexible documents where the storage contract calls for them.
Use the event bus for cross-feature work. Keep handlers thin and route work through feature-owned services.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| Feature architecture, APIs, repositories | [references/feature-architecture.md](references/feature-architecture.md) |
| End-to-end feature slice | [references/feature-slices.md](references/feature-slices.md) |
| Redis Streams, publish/request/reply | [references/event-bus.md](references/event-bus.md) |
| PostgreSQL/MongoDB ownership | [references/storage-ownership.md](references/storage-ownership.md) |
| Large documents, chat, analytics, write flows | [references/document-patterns.md](references/document-patterns.md) |
| Source layout or event details | [references/backend-layout.md](references/backend-layout.md) |
| Detailed Streams contract | [references/redis-streams.md](references/redis-streams.md) |

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
