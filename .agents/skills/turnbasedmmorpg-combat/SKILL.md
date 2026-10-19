---
name: turnbasedmmorpg-combat
description: Combat snapshots, resolver formulas, modifiers, triggers, and log rendering in TurnBasedMMORPG. Use for combat runtime or combat presentation contracts.
---

# TurnBasedMMORPG Combat

Keep snapshot construction, resolver calculations, and modifier aggregation in their owning layers. Do not precompute resolver-only values in catalogs or actor builders.
Preserve trigger DTO, catalog, merge, weapon, and event-text contracts when changing combat logs.

## Lifecycle, Fencing & Determinism (SG10-W1, SG10-W4)

Apply these principles to affected runtime work; verify the owning manager/commit contract rather than assuming all existing paths already meet them.

- **Lock Fencing & Revision Checks (SG10-W1)**: Combat session commits and state exchanges must verify lease ownership and snapshot revisions (`combat:rbc:*`) before writing to prevent stale workers from overwriting active rounds.
- **Deterministic Simulation (SG10-W4)**: The combat resolver and all combat simulations must use isolated `random.Random(seed)` instances. Never invoke global `random.seed()`. Stabilize unordered candidate collections before random selection; preserve deliberate action priority and execution order.
- **Bounded Redis Batch Writes (SG10-W4)**: Combat logs, actor projection snapshots, and round queues in Redis must enforce bounded batching and trimmed queues to prevent unbounded memory growth.

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
