# TurnBasedMMORPG Game Content

Keep item, monster, and character skill definitions in their owning catalogs and resources. Preserve ID and surface contracts across runtime, API, and UI.
Treat player-visible lore, balance, and visual intent as creative decisions; use project creative guidance when a choice is unresolved.

For combat feints, abilities and their event text, read the owner's
[temporary narrative-library retention decision](../../turnbasedmmorpg-combat/references/trigger-log-rendering.md).
The factual combat log does not require artistic action variants; optional event
texts remain in the existing library as a reserve. Do not remove body/weapon
narrative variants as cleanup. Keep mechanical validation and catalog names.

For Monster encounter orders, readiness/instance orchestration and other-domain consumers, use [the Monsters skill](../../turnbasedmmorpg-monsters/SKILL.md). Definitions and item catalogs remain owned here.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| New or restructured server catalog, bootstrap or visual-reference registry | [Project catalog conventions](../../turnbasedmmorpg-project/references/catalog-conventions.md) |
| Items, affixes, scaling, text resources | [../references/items.md](../references/items.md) |
| Monster family structure and equipment | [../references/monster-families.md](../references/monster-families.md) |
| Monster abilities, loot, combat compatibility | [../references/monster-abilities-and-compatibility.md](../references/monster-abilities-and-compatibility.md) |
| Character skill IDs and progression | [../references/skill-ids-and-progression.md](../references/skill-ids-and-progression.md) |
| Skill DTO/surface contracts or migration | [../references/skill-contracts-and-migration.md](../references/skill-contracts-and-migration.md) |
| AI generation identity and determinism | [../references/generation-determinism.md](../references/generation-determinism.md) |
| Lore and public library interface | [../references/lore-interface.md](../references/lore-interface.md) |
| Lore source map | [../references/source-map.md](../references/source-map.md) |

Read the referenced details for the task at hand. Verify implementation claims against current code and tests.
