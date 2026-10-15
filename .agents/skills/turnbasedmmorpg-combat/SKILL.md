---
name: turnbasedmmorpg-combat
description: Combat snapshots, resolver formulas, modifiers, triggers, and log rendering in TurnBasedMMORPG. Use for combat runtime or combat presentation contracts.
---

# TurnBasedMMORPG Combat

Keep snapshot construction, resolver calculations, and modifier aggregation in their owning layers. Do not precompute resolver-only values in catalogs or actor builders.
Preserve trigger DTO, catalog, merge, weapon, and event-text contracts when changing combat logs.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| Actor snapshots and loadout mapping | [references/snapshots.md](references/snapshots.md) |
| Resolver formulas, caps, branches | [references/resolver-math.md](references/resolver-math.md) |
| Modifiers, temporary effects, unarmed math | [references/modifiers-and-effects.md](references/modifiers-and-effects.md) |
| Known discrepancies and checks | [references/known-issues-and-checks.md](references/known-issues-and-checks.md) |
| Trigger DTOs and catalog keys | [references/trigger-contracts.md](references/trigger-contracts.md) |
| Trigger event text and log merge | [references/trigger-log-rendering.md](references/trigger-log-rendering.md) |
| Weapon triggers and adding a trigger | [references/weapon-triggers.md](references/weapon-triggers.md) |

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
