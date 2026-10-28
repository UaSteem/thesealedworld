# TurnBasedMMORPG Generation AI Determinism

## Read by task

| Change | Related reference |
| --- | --- |
| Item generation or text | .agents/skills/turnbasedmmorpg-game-content/references/items.md |
| Monster-owned generated content | .agents/skills/turnbasedmmorpg-game-content/references/monster-families.md |
| Infrastructure or cross-feature ownership | .agents/skills/turnbasedmmorpg-backend/references/feature-architecture.md |

The template identity rule below applies to both item and monster generation. Load only the related content reference for the current task.

## Core Rule

Separate template identity from prompt richness.

- Template hash payload is the minimal stable identity used to reuse generated output.
- Prompt payload may be richer and may include descriptive source context.
- Item instance ids, placement, locations, combat actor ids, affix rolls, transient runtime data, and raw `source_context` must not enter a reusable template hash unless the product owner explicitly makes that field part of template identity.

## Item Text Template Hash

Persisted item text templates are keyed only by:

```text
clan_id + base_id + item_tier (from material) + material_id + normalized affix lore tags + visual_variant_id
```

The hash function may wrap this payload with the prompt version so prompt-contract changes create a new template generation space.

Do not include in the item text template hash:

- `location_id`
- `source_tier`
- `owner_family` object
- `loot_culture` object
- `family_id` when `clan_id` is available
- `member_role`
- `variant_key`
- `item_id`
- placement data
- raw affix ids, bundles, or roll values (use normalized authored lore meanings instead)

Prompt payload may still include `source_context`, `owner_family`, and `loot_culture`; those fields help the AI write the text but do not define template identity.

As implemented by the v2 text contract, `resources/affixes/narrative.py` owns the controlled meanings.
Normalize only actually rolled affix identities; sort/deduplicate the resulting lore IDs.
The payload includes their meanings and selected appearance description; changes to prompt semantics require a prompt version change.
`material_tier` selects a material, and the chosen material determines item tier; do not use rarity to overwrite that derived tier.
Selected `appearance` and `is_identified` belong to the instance. AI readiness must not reveal text automatically.
New instance/template baseline text is catalog-derived rather than duplicated; public inventory projection gates prepared text on identification.
The authorized identify inventory action is implemented; an appraisal character skill is still deferred.

For the current legacy item AI text path, generated clan narrative still comes from the database by `clan_id`. The new prepared Python monster catalog exists, but this item consumer has not switched to it yet. Preserve the current generator until its narrative source is migrated explicitly.

- In this legacy item path, do not substitute static resources for a referenced persisted clan. The new prepared catalog is canonical for authored monster definitions, but legacy generated-clan UUIDs still refer to historical DB content.
- Do not trust an event-provided `owner_family` object as the source of truth for item prompt narrative.
- If `clan_id` is present, load the generated clan row and use its persisted `name_ru`, `description`, `raw_tags`, and `flavor_content.loot_culture`.
- If a `clan_id` is invalid or missing in the DB, fail the AI text task instead of falling back to static family resources or stale payload data.

## Monster Runtime Items

Monster runtime item projections are combat inputs, not player loot templates.

- Natural monster equipment such as claws, teeth, shells, or hides may exist as runtime combat projections.
- Natural equipment must not enqueue persisted item AI text.
- Natural equipment must not become player equipment loot by itself.
- Natural monsters drop resources, ingredients, salvage, or other configured loot resources, not persisted equipment instances.

## AI Task Identity

When an AI output belongs to a reusable template, prefer task identity based on the template hash or generated template id, not a concrete item instance id.

Using item instance ids in task identity is only correct when the generated output is truly unique to that item instance.

## Verification

For item text hash changes, run:

```powershell
.\.venv\Scripts\pytest.exe tests\backend\features\items\test_generation_service.py tests\backend\features\items\test_item_text_service.py --no-cov
```

Add focused tests proving that fields excluded from the template hash do not create new templates.
