## Waterfall Layer Rules

| Layer | Rule | Examples |
|---|---|---|
| `base` | Systemic or attribute-derived intrinsic baseline; numeric | `evasion.base = agility * 0.05`; hand accuracy bases stay `0.0` because hit baseline is resolver-owned |
| `source` | Stable pre-combat: items, affixes, passives, equipment properties | `{"item:sword_01": 12.0}` |
| `temp` | Runtime: buffs, debuffs, stances, control, round-local mutations | Applied by EffectService, cleared on effect expiry |

Current state: mapper sources can be plain numeric additive values or operation
commands such as `+x`, `-x`, `*x`, `/x`, and `=x`. Compiled item modifier
contracts can emit operation commands; older or direct mapper values may still
be plain numeric additions.

`temp` entries are written by `EffectService` using `ActiveEffectDTO.modified_keys` for
rollback. Waterfall is rebuilt after any temp change.

---

## Skill Scale

Skills in `ActorSnapshot.skills` and `ActorStats.skills` are **always 0..1 normalized**.

```python
skill_val = 0.0   # untrained
skill_val = 1.0   # fully trained (100%)
skill_val = 1.5   # overmastery via items/effects
```

UI display: `skill_val * 100` (as percent). Never divide by 100 in runtime math.

Correct usage in resolver:
```python
skill_multiplier = 1.0 + skill_val          # +100% at cap = 2× multiplier
chance = min(0.50, 0.25 + 0.25 * skill_dual_wield)  # 0.25 base, 0.50 at full mastery
```

---

## Offensive Branch Selection

`resolver.support.offensive_lookup.get_offensive_val(stats, ctx, key)` dispatches on `ctx.flags.meta.source_type`:

| source_type | damage_base | accuracy | armor_penetration_pct | crit_chance |
|---|---|---|---|---|
| `main_hand` | `main_hand_damage_base` | `0.60 + skill_bonus + main_hand_accuracy + accuracy` | `main_hand_armor_penetration_pct + armor_penetration_pct` | `main_hand_crit_chance + crit_chance` |
| `off_hand` | `off_hand_damage_base` | `0.60 + skill_bonus + off_hand_accuracy + accuracy` | `off_hand_armor_penetration_pct + armor_penetration_pct` | `off_hand_crit_chance + crit_chance` |
| `magic` | `magical_damage` | `0.60 + skill_bonus + magical_accuracy + accuracy` | `0.0` | `magical_crit_chance` (no global crit) |
| `item` | `item_damage_base` | `0.60 + skill_bonus + item_accuracy` | `item_armor_penetration_pct + armor_penetration_pct` | `item_crit_chance` |

`ContextBuilder._analyze_intent()` sets `source_type`:
- `strategy == "instant"` → `"magic"`
- `strategy == "item"` → `"item"`
- `strategy == "exchange"` → `"main_hand"` or `"off_hand"` from `external_mods.hand`

---

## Resolver Dependency Table

| Resolver reads | ActorStats path | Populated by | Status |
|---|---|---|---|
| accuracy (main) | `0.60 + weapon skill bonus + atk.mods.main_hand_accuracy + atk.mods.accuracy` | Resolver + CharMathModel / MonsterProfile modifiers | OK |
| accuracy (off) | `0.60 + weapon skill bonus + atk.mods.off_hand_accuracy + atk.mods.accuracy` | Resolver + CharMathModel / MonsterProfile modifiers | OK |
| accuracy (magic) | `0.60 + skill bonus + atk.mods.magical_accuracy + atk.mods.accuracy` | Resolver + CharMathModel / MonsterProfile modifiers | OK |
| damage_base (main) | `atk.mods.main_hand_damage_base` | CharMathModel / MonsterProfile | OK |
| damage_base (off) | `atk.mods.off_hand_damage_base` | CharMathModel / MonsterProfile | OK |
| damage_base (magic) | `atk.mods.magical_damage` | CharMathModel / MonsterProfile | OK |
| damage_spread (main/off/magic) | `atk.mods.{prefix}_damage_spread` | CharMathModel / MonsterProfile | OK |
| physical_suppression | `atk.mods.physical_suppression` | CharMathModel | OK |
| armor_penetration_pct (main/off/item) | `atk.mods.{source}_armor_penetration_pct + armor_penetration_pct` | CharMathModel | OK |
| armor_ignore_chance (main/off/item) | `atk.mods.{source}_armor_ignore_chance + armor_ignore_chance` | CharMathModel | OK |
| magical_penetration (magic/elemental) | `atk.mods.magical_penetration` | CharMathModel | OK |
| crit_chance (main/off) | `atk.mods.{prefix}_crit_chance + crit_chance` | CharMathModel | OK |
| crit_chance (magic) | `atk.mods.magical_crit_chance` only | CharMathModel | OK (asymmetric) |
| crit_cap (all) | `atk.mods.{prefix}_crit_cap` | DTO defaults | OK |
| physical_strength_power | `atk.mods.physical_strength_power` for weapon/style assembly | Waterfall from Strength | OK |
| physical_agility_power | `atk.mods.physical_agility_power` for weapon assembly | Waterfall from Agility | OK |
| physical_endurance_power | `atk.mods.physical_endurance_power` for survival and style-specific assembly | Waterfall from Endurance | OK |
| physical_damage | legacy/reserved flat field; weapon resolver does not add it automatically | DTO / compatibility | OK |
| physical_damage_bonus | `atk.mods.physical_damage_bonus` | CharMathModel | OK |
| evasion | `def.mods.evasion` | CharMathModel / MonsterProfile | OK |
| dodge_cap | `def.mods.dodge_cap` (default 0.75) | DTO default | OK |
| anti_dodge_chance | `atk.mods.anti_dodge_chance` | CharMathModel | OK |
| parry | `def.mods.parry` | CharMathModel | OK |
| parry_cap | `def.mods.parry_cap` (default 0.50) | DTO default | OK |
| block | `def.mods.block` | CharMathModel | OK |
| shield_block_cap | `def.mods.shield_block_cap` (default 0.75) | DTO default | OK |
| physical_resistance | `def.mods.physical_resistance` | CharMathModel / MonsterProfile | OK |
| armor | `def.mods.armor` | CharMathModel / MonsterProfile | OK |
| magic_armor | `def.mods.magic_armor` | CharMathModel jewelry power / MonsterProfile | OK |
| `{elem}_resistance` | `def.mods.{elem}_resistance` | CharMathModel / MonsterProfile | OK |
| magical_penetration (elemental) | `atk.mods.magical_penetration` | CharMathModel | OK |
| counter_attack_chance | `def.mods.counter_attack_chance` | CharMathModel | OK |
| counter_attack_cap | `def.mods.counter_attack_cap` (default 0.50) | DTO default | OK |
| skill_light/medium/heavy_armor | `def.skills.skill_{type}_armor` | Snapshot skills | OK |
| skill_{weapon_class} (crit mult) | `atk.skills.skill_{class}` | Snapshot skills | OK (formula bug) |
| healing base | `atk.mods.magical_damage` | CharMathModel | OK |

---

## Caps Table

| Field | DTO Default | Applied In |
|---|---|---|
| `dodge_cap` | 0.75 | `resolver._step_evasion_roll` |
| `parry_cap` | 0.50 | `resolver._step_parry_roll` |
| `shield_block_cap` | 0.75 | `resolver._step_block_roll` |
| `counter_attack_cap` | 0.50 | `resolver._step_counter_check` |
| `resistance_cap` | 0.85 | NOT in resolver — pending waterfall layer |
| `vampiric_trigger_cap` | 1.0 | NOT in resolver — trigger-driven, pending |
| `main_hand_crit_cap` | 0.75 | `resolver._step_critical_roll` |
| `off_hand_crit_cap` | 0.75 | `resolver._step_critical_roll` |
| `magical_crit_cap` | 0.75 | `resolver._step_critical_roll` |

---
