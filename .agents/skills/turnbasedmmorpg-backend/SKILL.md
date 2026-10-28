---
name: turnbasedmmorpg-backend
description: Backend feature ownership, persistence, Redis Streams, and cross-feature slices in TurnBasedMMORPG. Use for backend APIs, services, repositories, workers, or events.
---

# TurnBasedMMORPG Backend

Backend features own game behavior; feature integrations mediate infrastructure and cross-feature event-bus access. Infrastructure managers own Redis key spaces. PostgreSQL owns relational truth; MongoDB storage follows its documented contract. Enforce route audience authentication and character ownership. Multi-step changes require idempotency, durable commit ordering, failure recovery and fencing.

## Choose the route

- **Use this domain from a caller or adjacent domain:** read [Consumer contract](references/contract.md). Stay within supported entry points and handle documented limits/errors.
- **Change this domain:** read [Properties and implementation guidance](references/properties.md), then only the relevant thematic references.

This stage separates existing guidance structurally. Verify implementation claims against current code, tests and configuration; missing contract details remain pending substantive refresh.
