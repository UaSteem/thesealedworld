## Combat Catalog Integration

Weapon mastery skills link directly to the combat catalog via `weapon_class`:

- `context_builder.py` sets `ctx.flags.meta.weapon_class = skill_key.replace("skill_", "")` (e.g., `"skill_swords"` → `"swords"`)
- Basic exchange catalog keys follow the pattern `f"skill_{weapon_class}.{source_type}"` (e.g., `"skill_swords.main_hand"`)
- Basic exchange catalog module: `src/backend/features/game_catalog/combat/resources/basic_exchanges/`

When adding a new weapon mastery skill, also add a corresponding basic exchange entry in `basic_exchanges/definitions/weapon_mastery.py` with event texts for `use`, `hit`, `crit`, `miss`, `dodge`, `parry`, `block`.

## Surface Contracts

Keep `src/backend/features/game_catalog/skills/resources/contracts.py` in sync whenever a skill is added, renamed, removed, or starts/stops affecting a surface.

Current surfaces:

- `actor_snapshot`: combat skills plus `skill_adaptation`.
- `encounter`: `skill_scouting`, `skill_pathfinder`, `skill_hunting`, `skill_taming`.
- `crafting`: `skill_first_aid`, `skill_weapon_craft`, `skill_armor_craft`, `skill_jewelry_craft`, `skill_alchemy`, `skill_engineering`, `skill_artifact_craft`.
- `inventory`: combat equipment skills plus `skill_parrying`, `skill_weapon_craft`, `skill_armor_craft`, `skill_jewelry_craft`, `skill_engineering`.

Exploration/encounter should use explicit `skill_*` keys from the encounter contract. Treat aggregate reads such as `skills.get("survival")` as legacy or incorrect unless the project owner explicitly approves an aggregate contract.

## DTO Contracts

The active feature-owned DTO contract for character modifiers is:

- `src/backend/features/character/dto/modifiers.py`

The shared modifier DTO is legacy compatibility:

- `src/shared/schemas/modifier_dto.py`

Do not extend `src/shared/schemas/modifier_dto.py` as the canonical source of truth. If a consumer still imports the shared DTO, inspect that path carefully and prefer a scoped migration or compatibility note instead of spreading the legacy contract further.

## Reference Surfaces

When adding or renaming a skill, search beyond the catalog.

- Scenarios: JSON resources use `skills_queue` entries such as `push:skill_swords`; formatter exposes `catalog: skills` links.
- Monsters: family resources use per-variant `skills` lists; generated values are computed from monster tier.
- Items and inventory: item resources and shared item schemas use `related_skill`, `skill_key`, `weapon_skill_key`, or `armor_skill_key`.
- Combat loadout: `CharacterCombatActorInputBuilder` maps equipped items into combat layout skill ids; combat context consumes those layout ids.
- Actor snapshots: character snapshots flatten active session skills into `combat.skills`.
- Status UI: `CharacterStatusService` groups session skills by catalog `ui_group` and emits catalog links.
- Progression/persistence: character session and skill repository code store unlocked skill ids and values under `$.skills.<skill_key>`.

Use `rg -n "skill_[a-z_]+" src tests docs` as the first broad reference scan.

## Add Or Rename Workflow

For a new skill:

1. Add the `SkillDTO` in the correct `resources/definitions/*.py` file, or create a new definition file only if the existing UI/domain groups do not fit.
2. Add the definition group to `SKILL_GROUPS` if a new file was created.
3. Choose `category`, `group`, and `ui_group` deliberately:
   - `category`: broad `combat` vs `non_combat`.
   - `group`: storage/domain group, one of `combat`, `world`, `crafting`, `social`.
   - `ui_group`: display grouping such as `weapon_mastery`, `survival`, or `trade`.
4. Update `SKILL_SURFACE_CONTRACTS` if any runtime surface needs the skill.
5. Update active DTO fields only when typed combat/status consumers require a fixed field.
6. Update scenario rewards, monster kits, item `related_skill` fields, combat loadout mapping, status UI expectations, and docs as needed.
7. Update catalog tests so the documented key set matches the actual catalog.

For a rename:

1. Treat it as a breaking catalog migration.
2. Replace every reference in definitions, tests, surface contracts, scenarios, monsters, items, snapshots/loadout code, status UI, and docs.
3. Decide whether persisted active sessions or DB skill progress rows need a migration or compatibility alias.
4. Verify no old id remains with `rg -n "<old_skill_id>" src tests docs`.

## Known Docs/Code Disagreements

Record these when planning skill work:

- Some docs use `Skill / 100`; canonical internal runtime/storage values are normalized `0.0..1.0`.
- Some combat resolver paths still divide by `100.0`; inspect before relying on those formulas.
- Exploration currently has legacy aggregate reads such as `skills.get("survival")`; intended contract is explicit `skill_*` keys.
- `docs/game-design/rules/skills/catalog_reference.md` preserves the reviewed
  current catalog weights; do not resurrect old generic rows that have no
  catalog id.
- Scenario designer docs mention `skill_power_strike`, which is not a catalog skill.
- Combat still imports `src/shared/schemas/modifier_dto.py` in some places even though the active owner is the character feature DTO.

## Common Mistakes

- Adding a skill id without the `skill_` prefix.
- Updating design docs but not catalog tests.
- Adding an id to scenarios, monsters, or items before it exists in `SkillCatalogService`.
- Treating `ui_group` as the storage/domain group.
- Using aggregate keys like `survival` in runtime checks.
- Assuming player-facing `0..100` display values are stored internally.
- Extending the shared legacy modifier DTO as if it were the active contract.
- Renaming a skill without checking scenario resources, monster resources, item `related_skill`, combat loadout, actor snapshots, and status UI.

## Verification

Run the narrowest relevant tests first:

```powershell
.\.venv\Scripts\pytest.exe tests\backend\features\game_catalog\skills --no-cov
.\.venv\Scripts\pytest.exe tests\backend\features\scenario\test_awakening_rift_catalog_contract.py --no-cov
.\.venv\Scripts\pytest.exe tests\backend\features\character\runtime tests\backend\features\character\test_status_service.py --no-cov
```

If scenarios, monsters, or items were touched, also run their catalog/contract tests or add focused tests before finishing.
