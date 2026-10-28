---
name: turnbasedmmorpg-combat
description: Combat snapshots, resolver formulas, modifiers, triggers, and log rendering in TurnBasedMMORPG. Use for combat consumer integration, runtime, or presentation contracts.
---

# TurnBasedMMORPG Combat

Keep snapshot construction, resolver calculations and modifier aggregation in their owning layers; do not precompute resolver-only values in catalogs or actor builders. Preserve trigger/log contracts. Runtime changes require lease/revision fencing, isolated seeded RNG and bounded Redis batches; verify the owning commit contract.

## Choose the route

- **Use this domain from a caller or adjacent domain:** read [Consumer contract](references/contract.md). Stay within supported entry points and handle documented limits/errors.
- **Change this domain:** read [Properties and implementation guidance](references/properties.md), then only the relevant thematic references.

This stage separates existing guidance structurally. Verify implementation claims against current code, tests and configuration; missing contract details remain pending substantive refresh.
