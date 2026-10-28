---
name: turnbasedmmorpg-game-content
description: Item, monster, character skill catalog, generation, and lore contracts in TurnBasedMMORPG. Use for game content or catalog changes.
---

# TurnBasedMMORPG Game Content

Keep item, monster and character skill definitions in their owning catalogs/resources and preserve IDs and runtime/API/UI surfaces. Lore, balance and visual intent require project creative guidance when unresolved. Monsters owns encounter orders/readiness/instance orchestration; Combat owns battle execution.

## Choose the route

- **Use this domain from a caller or adjacent domain:** read [Consumer contract](references/contract.md). Stay within supported entry points and handle documented limits/errors.
- **Change this domain:** read [Properties and implementation guidance](references/properties.md), then only the relevant thematic references.

This stage separates existing guidance structurally. Verify implementation claims against current code, tests and configuration; missing contract details remain pending substantive refresh.
