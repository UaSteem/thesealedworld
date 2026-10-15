# Combat Contract Skill

This skill teaches agents where combat formulas belong, where snapshot mapping
belongs, and how to avoid duplicating resolver or waterfall work in catalogs or
actor builders.

Read this skill before touching:
- `src/backend/features/combat/runtime/engine/resolver.py`
- `src/backend/features/combat/runtime/engine/context_builder.py`
- `src/shared/schemas/modifier_dto.py`
- `src/backend/features/character/runtime/combat_math_model.py`
- `src/backend/features/monsters/instances/runtime/combat_math_model.py`
- `src/backend/core/calculators/stats_waterfall_calculator.py`

Also read:
- `docs/game-design/rules/modifiers/actor_mapper_reference.md`
- `docs/game-design/rules/modifiers/modifier_vocabulary.md`

---

## Architecture Map — Who Owns What

```
Character / Monster builder
  combat_math_model.py         (CharacterCombatMathModelBuilder)
  combat_profile.py            (build_monster_combat_context)
        │
        │  writes raw.attributes and raw.modifiers
        │  each modifier: { base: float, source: {key: float}, temp: {} }
        ▼
StatsWaterfallCalculator
  src/backend/core/calculators/stats_waterfall_calculator.py
        │
        │  sums base + source values + temp values → flat modifier values
        ▼
BasePowerAssembler
  src/backend/features/combat/runtime/engine/base_power_assembler.py
        │
        │  turns weapon power + weighted stat power + mastery into final hand base
        │  called once on session entry, then on dirty_stats after effect apply/remove
        ▼
ActorStats  (in-memory only, not persisted to Redis)
  .mods:   CombatModifiersDTO  ← flat floats, post-waterfall
  .skills: CombatSkillsDTO     ← flat floats, 0..1 scale
        │
        ▼
AbilityService / EffectService  (between Collector and Executor)
        │  applies ActiveEffectDTO to raw.modifiers.temp
        │  marks dirty_stats, triggers waterfall rebuild
        ▼
CombatResolver.resolve_exchange(atk_stats, def_stats, context)
        │  reads ONLY ActorStats.mods and ActorStats.skills
        │  no raw.modifiers access, no Redis, no DB
        ▼
InteractionResultDTO
```

---

## ActorSnapshot Contract

### What Must Be Populated BEFORE Any Exchange

| Snapshot Field | Populated By | Content |
|---|---|---|
| `meta.hp/en/tactics/tokens/feints` | Session/Lifecycle service | Current hot state |
| `raw.attributes` | Character/Monster builder | `{key: {base, source:{}, temp:{}}}` |
| `raw.modifiers` | Character/Monster builder | `{key: {base, source:{label:float}, temp:{}}}` |
| `skills` | Snapshot builder | `{skill_key: float}`, scale **0..1** |
| `loadout.layout` | Character/Monster builder | `{slot: skill_key, slot_trigger: trigger_id}` |
| `loadout.known_abilities` | Snapshot builder | `list[ability_id]` |
| `statuses.abilities/effects` | Combat runtime per round | ActiveAbilityDTO / ActiveEffectDTO |
| `stats` (ActorStats) | WaterfallCalculator | Rebuilt before each exchange if dirty |

### What Is Calculated INSIDE Resolver (Never Pre-Compute These)

- Accuracy roll: `(0.60 + min(skill_val, 1.0) * 0.40 + source_accuracy_modifier) * ctx.mods.accuracy_mult`, clamped to `0..1`
- Crit roll: `(hand_crit_chance + global_crit_chance) * (1.0 + skill_val)`
- Evasion check: `min(evasion - atk.anti_dodge_chance, dodge_cap)`
- Parry check: `min(parry * (1 + PARRY_SKILL_MULT_PER_POINT * skill_parrying), parry_cap)`
- Shield defenders disable the evasion stage when the off-hand style is
  `skill_shield_mastery`.
- Shield block check derives from shield power, uncapped evasion, and shield
  mastery gate: `min(power * PB * (1 + evasion * EB) * G * shield_block_chance_mult, BC0 + BCM * mastery)`.
- Successful shield blocks add temporary guard armor for that hit:
  `(shield_power + physical_endurance_power) * AR * G * max(Kmin, 1 - evasion * EC) * shield_guard_power_mult`.
- Successful shield blocks can open a non-recursive instant shield counter:
  `min(counter_attack_chance * G, 0.50)` for half main-hand damage gated by `G`,
  with normal mitigation and no accuracy/evasion/parry/block/crit checks.
- Shield counters apply `shield_opening` to the attacker; it reduces evasion
  and parry through pipeline multipliers and expires only after the next
  exchange with the tank that applied it.
- Counter check: `min(counter_attack_chance, counter_attack_cap)`
- Weapon damage: `rand((assembled_base + physical_damage_bonus)*(1-spread), ... ) - resist - armor`.
- Elemental/magic damage: `rand(magical_damage*(1-spread), ...) - elemental_resist - magic_armor`.
- Assembled weapon base: `weapon_power + ((strength_power*wS + agility_power*wA) * mastery_factor)`.
  Weapon classes use normalized effective Strength/Agility damage weights that sum to `1.0`.
- Unarmed damage: `rand((strength_base * unarmed_efficiency + physical_damage_bonus)*(1-spread), ... ) - resist - armor`; unarmed does not add `physical_damage` twice.
- Healing: `rand(magical_damage*0.9, magical_damage*1.1) [* 1.5 if crit]`

Mass-target feints use the normal resolver for every concrete target. The
primary target is the exchange target; secondary targets are executor-created
`unidirectional` interactions with `feint_role="secondary"`, `pay_cost=False`,
and `generate_feints=False`. They keep physical hit/defense/armor checks but do
not advance exchange counters, do not return target-queue pairs, and do not
create counter/off-hand chain tasks.

---

## Loadout Layout Structure

```python
loadout.layout = {
    "main_hand":         "skill_swords",           # weapon mastery skill key
    "main_hand_trigger": "accuracy.true_strike",   # trigger ID: "section.field" or bare name
    "off_hand":          "skill_shield",            # or "skill_dual_wield" for a weapon
    "off_hand_trigger":  "crit.bleed_proc",
    "body":              "skill_heavy_armor",       # / skill_medium_armor / skill_light_armor
}
```

`ContextBuilder._analyze_intent()` reads `loadout.layout` to set `ctx.flags.meta.source_type`
and `ctx.flags.meta.weapon_class`. `ContextBuilder._analyze_defense()` reads `body` and
`off_hand` to set mastery flags.

Dual wield triggers when `source_type == "main_hand"` and `off_hand` is a non-shield skill.
Chance: `min(0.50, 0.25 + 0.25 * skill_dual_wield)` (normalized, no multiplier).

---
