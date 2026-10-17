# TurnBasedMMORPG Monster Family

## Read by task

| Change | Sources to inspect |
| --- | --- |
| Family shape, variant, role, or registration | src/backend/features/monsters/catalog/contracts.py; src/backend/features/monsters/catalog/resources/monster_structs.py; src/backend/features/monsters/catalog/families; src/backend/features/monsters/catalog/registry.py; src/backend/features/monsters/catalog/materialization/clan_factory.py |
| Generation fields | src/backend/features/monsters/catalog/materialization/generation_fields.py; tests/backend/features/monsters/catalog/materialization/test_generation_fields.py |
| Combat actor or equipment mapping | src/backend/features/monsters/instances/runtime/combat_actor_input.py; tests/backend/features/monsters/instances/runtime/test_combat_actor_input.py; .agents/skills/turnbasedmmorpg-combat/references/snapshots.md |
| Numeric monster skills | src/backend/features/monsters/catalog/skill_contract.py; src/backend/features/game_catalog/skills; .agents/skills/turnbasedmmorpg-game-content/references/skill-ids-and-progression.md |
| Monster item inputs | src/backend/features/items/resources/bases.py; .agents/skills/turnbasedmmorpg-game-content/references/items.md |

Read project or backend architecture references when changing ownership, infrastructure access, or cross-feature contracts. For a focused family resource edit, inspect only the relevant rows above.

## Prepared Python catalog

The canonical read catalog uses `FamilyDefinition`, `ClanDefinition`, and `MemberDefinition` in `src/backend/features/monsters/catalog/contracts.py`. Explicit base clans are registered in `catalog/prepared.py`; starter asset references live with their clan variants, historical presentation references remain in `catalog/presentation.py`, memory indices in `catalog/indexes.py`, validation in `catalog/validation.py`, and public reads in `catalog/registry.py` (`get_catalog`, `get_catalog_family`, `get_catalog_clan`, `get_catalog_member`).

- Wolves, rats, goblins and bandits are authored through nested immutable DTOs in `catalog/nested_contracts.py` and `catalog/families/{wolf,rat,goblin,bandit}_catalog/`: `bases/` owns shared statistics, loadout, tier range and spawn weight; `clans/base/members/` owns explicit names, tags, art, skills and separate `ability_ids`. `resolve_family` resolves one basis reference into existing read definitions. The active starter catalog must not load historical family literals or presentation maps. Anchors deliberately retain the historical literal/authoring path and remain excluded from normal spawning. Do not create duplicate authored statistics for clan variants.
- Current starter ability IDs are empty. Skills remain numeric skill availability; adding an authored ability ID does not implement its execution in Combat.
- Studio/API expose `base_id` and `ability_ids` separately. Catalog loading remains independent of persistence, and old generated DB records are preserved.
- Clan IDs and qualified member IDs are authored constants, independent of location, habitat, and DB UUIDs. A member definition is not a spawned instance.
- Legacy `MonsterFamilyDTO` readers use an explicit base-clan adapter returning fresh mutable DTOs. New clan-aware consumers must use qualified catalog reads.
- Loading the prepared catalog requires no DB, provider, runtime JSON file, or S3 request. Image references carry asset IDs/source paths/review status; publishing them is a separate step.
- The old persisted-monster group/materialization/rebuild pipeline is permanently guarded by `monsters/runtime_retirement.py` in the monster-alpha branch. World/rift requests fail explicitly before accessing old data; startup does not materialize monster pools. New catalog-driven encounter runtime is not implemented yet. Catalog/Studio/bootstrap and the separate anchor projection path remain available.
- Existing statistics, roles, skills, equipment, tiers and versions must remain unchanged unless separately authorized. Legacy local generated DB rows have been exported and removed; use `archive/data_retirement/INDEX.md` for the verified snapshot and cleanup receipt.

## Ownership

- Family resources live in `src/backend/features/monsters/catalog/families/*.py`.
- The active registry is owned by `src/backend/features/monsters/catalog/registry.py`.
- Only families imported into `ALL_FAMILIES_RAW` are runtime-loaded. Many dormant family modules are DTO-valid but unavailable to spawning/combat until registered.
- Spawn biome/tier availability lives in `src/backend/features/monsters/encounters/resources/spawn_config.py`, but spawn config does not register a family by itself.
- Monster item inputs flow through the item-generation/runtime item projection path. Do not model monsters as full player paperdolls.

## Family Shape

Use the new definitions for the prepared catalog and `MonsterFamilyDTO` only for the transitional legacy mechanics adapter. `monster_structs.py` is a typing aid and contains some legacy fields that DTO/runtime ignore.

Required top-level fields:

- `id`: stable lowercase snake case family id.
- `archetype`: one of `humanoid`, `beast`, `undead`, `construct`, `demon`, `unknown`.
- `organization_type`: one of `solitary`, `pack`, `gang`, `clan`, `legion`, `horde`, `swarm`.
- `hierarchy`: role buckets that reference variant ids.
- `variants`: mapping of variant key to variant object.

Effectively required for combat-ready families:

- `loot_profile`
- each combat-ready variant has an explicit `skills` list

Defaulted or optional fields:

- Top level: `default_tags`, `loot_profile`, `clan_model`, `member_models`.
- Variant: `extra_tags`, `min_tier`, `max_tier`, `fixed_loadout`, `skills`, `member_model`.

Do not add old/future-hook fields such as `ability_map`, `combat_profile`, `ability_overrides`, `body_loadout`, `equipment_scaling`, or `modifier_formula` unless the runtime DTOs and consumers are implemented in the same task.

## Variants And Roles

Roles are only:

- `minion`
- `veteran`
- `elite`
- `boss`

Each variant must define:

- `id`
- `role`
- `narrative_hint`
- `cost`
- `base_stats`

Rules:

- `hierarchy` entries must reference existing variant ids. DTO validation enforces this.
- Keep the variant dict key equal to `variant.id`; current DTO validation does not enforce this, but registry and generated monster code assume stable ids.
- Use `min_tier` and `max_tier` to gate variant availability. `get_available_variants_for_tier_window()` may include neighbor-tier variants around the current tier.
- `base_stats` must include `strength`, `agility`, `endurance`, `intellect`, `memory`, `mental`, `perception`, `projection`, and `prediction`.
- Put combat skill availability in `variant.skills`; do not store skill percentages in resources.

## Skills

Skills are numeric, trainable game skills. They are not abilities.

Monster resources store skill availability, not skill percentages.

- `variant.skills` is the explicit skill set for that monster variant.
- `member_model.skill_profile.base` may add skill keys for generated member models.
- Generated skill values are computed centrally from `member_tier / 7`, capped at `1.0`.
- Current generated monster skills are filtered through `filter_monster_combat_skills()` and only actor-snapshot combat skill keys are kept.

Use only real catalog ids such as `skill_unarmed`, `skill_archery`, or `skill_light_armor`; do not use ability ids, aggregate keys such as `survival`, or invented monster ability names in skill maps.

## Equipment And Loadouts

Monster combat loadouts are intentionally narrow. Do not expand monsters into a full humanoid paperdoll.

Allowed combat-facing equipment slots for current monster design:

- `main_hand`
- `off_hand`
- `body`
- one jewelry/accessory slot, represented in resources as `amulet`, for natural beast foci that map item `power` to flat `magic_armor`

Do not add or normalize toward `head_armor`, `arms_armor`, `legs_armor`, `feetwear`, rings, belt, or other full gear slots. The project intentionally concentrates item power into fewer item slots with larger affix capacity instead of spreading power across a full equipment doll.

`body` is equipment, not an abstract defensive layer or a path toward full paperdoll gear. It maps to a base item exactly like the hand slots, and item generation later enriches that base item with material, quality, affixes, triggers, and source context.

Humanoids and other item-using monsters may provide base item/loadout intent for `main_hand`, `off_hand`, and `body`. Monster families should not hand-author final generated item stats when the item generator owns that enrichment.

Every referenced item id must resolve through item resources/generation. Validate references when editing families.

Humanoid/item-using families should use item/equipment drop profiles. Beast and non-equipment monsters should use ingredient/material/salvage profiles.

## Catalog search and metadata bootstrap

`catalog/search.py` owns `CatalogSearchService` and immutable `MonsterSearchFilters`. Import from `monsters.catalog` or `monsters.public`. Search intersects ID/tag filters and returns deterministic immutable members; it does not perform random selection, party assembly or instance creation. Empty filters are unrestricted; system clans require explicit inclusion.

`catalog/bootstrap.py` projects presentation-only metadata into `bootstrap_contracts.py` DTOs. The protected GET `/api/admin/monsters/catalog/bootstrap` supports content-derived version/section hashes and ETag revalidation. It omits internal source paths and numerical mechanics. This does not wire the frontend cache or replace game_catalog bootstrap. Never expose service credentials to browser code. See `docs/planning/tasks/monster_catalog_search.md`.

## Authored texts and artwork inheritance

Four starter families use text_id references to `catalog/resources/texts.py` and its locale-keyed LANGUAGE_TEXTS. Write new prose, never import archived generated narratives. Add translations as data keyed by locale and stable text IDs; resolve through `catalog/texts.py` with mandatory ru fallback. Inspection/bootstrap accept locale; bootstrap schema2 hashes include locale metadata. Anchors keep their historical definitions.

Current accepted art is on MemberBaseDTO.default_image; MemberVariantDTO.image is optional unique artwork. resolve_family chooses variant art before basis default and exposes image_source. Do not duplicate fallback logic in clients. Do not change numeric stats, loadout, skills or tier availability while editing prose/art.

Tier projection is a separate next step, not implemented by localization. Old attributes had no implicit tier growth without an explicit profile; current availability remains unchanged. See `docs/planning/tasks/monster_texts_and_art.md` and `monster_tier_projection_design.md`.

## Family equipment references (goblins first)

Goblins own equipment entries and reusable sets under `families/goblin_catalog/equipment/`. These are references to existing item base IDs, not duplicate item mechanics. `equipment_contracts.py` validates references and slot compatibility through the public ItemCatalogService facade.

A goblin basis uses equipment_set_id instead of inline loadout. ClanDTO.equipment_overrides maps basis IDs to sets owned by the same family; this is full replacement, not layered merging. resolve_family produces the unchanged fixed_loadout plus equipment_set_id/equipment_source metadata for inspection/Studio. Other families retain inline loadouts. Do not add tier scaling, new affixes or change base stats as part of equipment organization. See `docs/planning/tasks/goblin_equipment_catalog.md`.
