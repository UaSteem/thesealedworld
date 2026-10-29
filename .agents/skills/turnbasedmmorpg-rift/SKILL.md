---
name: turnbasedmmorpg-rift
description: Rift generation language and approved implementation boundaries in TurnBasedMMORPG. Use for rift design, metadata, routes, or runtime work.
---

# TurnBasedMMORPG Rift

Approved stages outrank exploratory notes. Legacy node Rift contracts require explicit owner decisions; Hex Rift stays dev-only behind flags, limits and edge blocking. Keep generation metadata separate from live progress. Do not freeze persistence, final API/DTOs, Redis shapes or combat-return behavior without the applicable owner decision. Use isolated seeded RNG and stable candidate ordering.

Before adding or retaining a workaround as the chosen design, follow [the workaround decision rule](../turnbasedmmorpg-project/references/compatibility-decisions.md); it also covers assets, rendering, prototypes and labs. Discuss an unresolved bypass before implementing it; do not re-approve an already explicit owner choice.

## Choose the route

- **Use this domain from a caller or adjacent domain:** read [Consumer contract](references/contract.md). Stay within supported entry points and handle documented limits/errors.
- **Change this domain:** read [Properties and implementation guidance](references/properties.md), then only the relevant thematic references.

This stage separates existing guidance structurally. Verify implementation claims against current code, tests and configuration; missing contract details remain pending substantive refresh.
