## Modifier Key Status

### Active — Used by Resolver Or Base-Power Assembly

```
main_hand_damage_base    main_hand_damage_spread    main_hand_weapon_power
main_hand_stat_damage_raw main_hand_stat_damage_effective main_hand_mastery_factor
main_hand_damage_spread_raw main_hand_accuracy
main_hand_crit_chance    main_hand_armor_penetration_pct
main_hand_armor_ignore_chance
off_hand_damage_base     off_hand_damage_spread     off_hand_weapon_power
off_hand_stat_damage_raw off_hand_stat_damage_effective off_hand_mastery_factor
off_hand_damage_spread_raw off_hand_accuracy
off_hand_crit_chance     off_hand_armor_penetration_pct
off_hand_armor_ignore_chance
item_damage_base         item_accuracy              item_crit_chance
item_armor_penetration_pct item_armor_ignore_chance
magical_damage           magical_damage_spread      magical_accuracy
magical_crit_chance      magical_penetration
accuracy                 crit_chance                physical_suppression
armor_penetration_pct    armor_penetration_flat     armor_ignore_chance
physical_strength_power  physical_agility_power     physical_endurance_power
physical_damage_bonus
evasion                  dodge_cap                  anti_dodge_chance
parry                    parry_cap
block                    shield_block_cap
physical_resistance      armor                    magic_armor
shield_guard_power
shield_style_guard_power_raw shield_style_guard_power_bonus
{fire|water|air|earth|light|dark|arcane|nature}_resistance
counter_attack_chance    counter_attack_cap
```

### Pending — In DTO, Not Yet Applied by Resolver

```
main_hand_crit_cap       off_hand_crit_cap          magical_crit_cap
resistance_cap           vampiric_trigger_cap
main_hand_damage_bonus   off_hand_damage_bonus
healing_power
{elem}_damage_bonus                                   (elemental attack bonus, pending)
item_damage_bonus
```

### Renamed (Aliases Active in Both Mappers)

```
dodge_chance       → evasion
parry_chance       → parry
damage_reduction_flat → armor
magical_armor        → magic_armor
magical_damage_base   → magical_damage    (old design docs used this name)
magical_resistance    → magic_resist
```

---

## Unarmed / Strength Interaction

Strength flows into `physical_strength_power` through the attribute waterfall.
Agility and Endurance flow into their own physical power fields. For weapon
attacks, `BasePowerAssembler` combines weapon power, class-specific normalized
effective Strength/Agility damage weights, and weapon mastery into the final
hand damage base before `ActorStats` is created. Endurance does not feed
ordinary weapon damage; it stays available for survival and style-specific
mechanics. The resolver reads that assembled base and does not add
`physical_damage`.

For unarmed attacks, the mapper already uses Strength as `main_hand_damage_base`,
so `BasePowerAssembler` skips the `unarmed` class and the resolver applies the
`skill_unarmed` efficiency curve.

```python
# CharacterCombatMathModelBuilder._apply_unarmed_base:
main_hand_damage_base.base = strength           # strength value
main_hand_damage_spread.base = 0.50             # 50% spread
main_hand_accuracy.base = 0.0                   # hit baseline lives in resolver
```

Unarmed resolver curve:

```python
efficiency = 0.5 + (2.5 * skill_unarmed)        # 0.5x -> 3.0x
spread = max(0.10, 0.50 - (0.40 * skill_unarmed))
```

---

## Temp Effects, Buffs, Debuffs

Temp state is in `ActorSnapshot.statuses`:
- `ActiveAbilityDTO` — stances, channeling; stores `modified_keys: list[str]` for rollback
- `ActiveEffectDTO` — buffs, debuffs, control; stores `modified_keys` and `impact`

EffectService writes to `raw.modifiers[key]["temp"][effect_uid]`. After write it sets
`dirty_stats` and calls WaterfallCalculator to rebuild `ActorStats`. Resolver never reads
raw.modifiers directly — it always works with already-rebuilt stats.

Round-local mutations from triggers (via `_apply_mutation`) write to `ctx.flags`, `ctx.mods`,
or `ctx.stages` — these are pipeline-local and do NOT persist to the snapshot.

---

## Support Skills and Incoming Healing

`character/runtime/rules/support_skills.py` emits normalized rules for the
waterfall. Tactics scales only attribute-derived evasion, anti-dodge and counter
chance; direct item modifier bonuses are not scaled. Anatomy scales natural
HP/Energy regen separately for outside/combat and adds incoming-healing bonus.
Use the formulas in `docs/game-design/rules/skills/combat_runtime_reference.md`.
Stamina, existing caps/counter windows and monster zero HP regen stay intact.

`received_healing_bonus` is active: `engine/received_healing.py` scales planned
HP healing once in direct/prepared/shield/item/HOT/lifesteal producers. Explicit
resource applications identify the recipient. Commit only applies/clamps the
result; do not scale again in `_apply_resource_delta`, or scale passive regen.
AC vitals must resolve persisted plus pending skills through the same builder.
Rebuild frozen raw/snapshots for the current combat math version when comparing
new skill behavior. Use `test_combat_support_execution.py` for the real pipeline.
