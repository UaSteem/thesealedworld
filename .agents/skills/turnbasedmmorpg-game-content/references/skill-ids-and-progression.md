# TurnBasedMMORPG Skill Catalog

## Read by task

| Change | Sources to inspect |
| --- | --- |
| Skill IDs, definitions, groups, or UI keys | src/backend/features/game_catalog/skills; docs/game-design/rules/skills/catalog_reference.md; tests/backend/features/game_catalog/skills |
| Progression and value math | docs/game-design/rules/skills/progression_reference.md; current catalog implementation |
| Combat runtime skill use | docs/game-design/rules/skills/combat_runtime_reference.md; src/backend/features/combat/dto/actor.py; src/backend/features/combat/runtime/engine; .agents/skills/turnbasedmmorpg-combat/references/resolver-math.md |
| DTO or shared modifier contract | src/backend/features/character/dto/modifiers.py; src/shared/schemas/modifier_dto.py; .agents/skills/turnbasedmmorpg-game-content/references/skill-contracts-and-migration.md |

For a runtime consumer, inspect only its row:

| Consumer | Sources to inspect |
| --- | --- |
| Character session or snapshot | src/backend/features/character/schemas/session.py; src/backend/features/character/managers/session.py; src/backend/features/character/runtime/combat_actor_input.py; src/backend/features/character/runtime/combat_math_model.py |
| Combat | src/backend/features/combat/dto/actor.py; src/backend/features/combat/runtime/engine |
| Exploration or encounter | src/backend/features/exploration/services; src/backend/features/exploration/runtime |
| Scenario rewards | src/backend/features/scenario/resources/json; src/backend/features/scenario/engine/formatter.py |
| Items or inventory | src/backend/features/items/resources; src/shared/schemas/item.py |
| Monsters | src/backend/features/monsters/catalog/families |
| Status UI | src/backend/features/character/services/status_service.py; src/frontend/templates/game/components/panel/widgets/skill_groups.html |

Read backend or project architecture references when changing ownership or cross-feature contracts.


## Ownership

The canonical skill catalog is owned by `src/backend/features/game_catalog/skills`.

- Skill definitions live in `resources/definitions/*.py`.
- `SkillDefinitionDTO`, `SkillCategory`, `SkillGroup`, and `SkillUiGroup` live in `dto/catalog.py`.
- `SkillCatalogService` is the read API for catalog lookups and public text projection.
- `resources/contracts.py` owns surface-specific key lists for actor snapshots, encounters, crafting, and inventory.
- `tests/backend/features/game_catalog/skills/test_catalog_service.py` is the primary guard that catalog ids, groups, UI groups, and surface contracts stay coherent.

Do not move the catalog into `shared`. Shared code may contain compatibility DTOs, but the catalog itself is backend feature-owned.

## Current Skill IDs

Use these exact ids unless a rename task explicitly updates every reference.

Combat:

- Weapon Mastery: `skill_swords`, `skill_fencing`, `skill_polearms`, `skill_macing`, `skill_archery`, `skill_unarmed`
- Tactical: `skill_ranged_combat`, `skill_two_handed`, `skill_shield_mastery`, `skill_dual_wield`
- Armor: `skill_light_armor`, `skill_medium_armor`, `skill_heavy_armor`
- Combat Support: `skill_parrying`, `skill_anatomy`, `skill_tactics`

Crafting:

- `skill_first_aid`, `skill_weapon_craft`, `skill_armor_craft`, `skill_jewelry_craft`, `skill_alchemy`, `skill_engineering`, `skill_artifact_craft`

World:

- Gathering: `skill_mining`, `skill_herbalism`, `skill_skinning`, `skill_woodcutting`, `skill_hunting`, `skill_archaeology`
- Survival: `skill_taming`, `skill_adaptation`, `skill_scouting`, `skill_pathfinder`

Social:

- Trade: `skill_accounting`, `skill_brokerage`, `skill_contracts`, `skill_trade_relations`
- Leadership: `skill_leadership`, `skill_organization`, `skill_team_spirit`, `skill_egoism`

## Naming Rules

Every skill id must be lowercase snake case and must start with `skill_`.

The prefix is mandatory because:

- `load_skill_definitions()` rejects unprefixed ids.
- Catalog tests assert every skill id is prefixed.
- Combat context derives weapon class by stripping `skill_`, for example `skill_swords` becomes `swords`.
- Items, scenario rewards, actor snapshots, monster kits, combat loadout, and status UI use `skill_*` as stable catalog keys.

Do not add aggregate ids such as `survival`, category ids such as `crafting`, or ability-style ids such as `skill_power_strike` to the skill catalog unless they are real catalog skills and all references/tests are updated.

## Value Scale

Internal skill values are normalized floats in `0.0..1.0`.

- Store active character session and actor snapshot values as normalized floats.
- Runtime formulas should consume normalized values directly.
- UI, design docs, and player-facing text may display the same value as `0..100`; that is a presentation conversion only.
- If a formula or doc says `Skill / 100`, verify whether it is legacy `0..100` wording before copying it into runtime code.

Known scale risks:

- Some older combat formulas still divide skill values by `100.0`.
- Some design docs describe skill progression as `0..100`.
- New code must not mix `0.0..1.0` and `0..100` without an explicit conversion at the boundary.

## UI Display Rule

`display_value = round(skill_value * 100, 1)` — UI and player-facing text shows `0..100` (percent of mastery), the internal representation is always `0.0..1.0`.

Never pass raw `0.0..1.0` values to UI templates. Never store `0..100` display values in Redis or DTOs.

## Progression Model

Skills grow via a Ultima Online–style formula: using a skill awards XP, but growth slows as the skill value rises (diminishing returns):

```
delta = (base_power × global_rate × rate_mod) / (1 + current_skill × effective_wall)
```

- `global_rate = 0.00005` — current alpha base growth speed per action
- `effective_wall = global_wall × wall_mod` — difficulty ceiling (default `100.0`)
- `current_skill` — current normalized value (`0.0..1.0`)
- At `skill = 1.0` the denominator is `1 + 100 = 101`, delta approaches zero

Implementation: `src/backend/core/calculators/skill_progression_calculator.py` → `SkillProgressionCalculator.calculate_delta()`.

`base_power` is derived from character attribute weights defined on the `SkillDTO` (`stat_weights`). `action_power` is provided per action (e.g., combat exchange grants `1.0`, crafting may vary).

Do not implement custom progression math. Use `SkillProgressionCalculator` for all XP delta computation.
