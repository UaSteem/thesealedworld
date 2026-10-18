"""Read-only, deterministic support-skill recovery diagnosis. No DB or Redis.

Run from repository root: python -m tools.diagnostics.probe_support_skills_recovery
The output records current behavior; it does not encode proposed coefficients.
"""

from __future__ import annotations

import json

from src.backend.features.character.runtime.rules.vital_constants import REGEN_TICK_SECONDS
from src.backend.features.character.runtime.vitals import CharacterVitalsCalculator
from src.backend.features.character.schemas.session import CharacterSessionVitalsDTO, VitalValueDTO
from src.backend.features.combat.dto.actor import ActiveEffectDTO, ActorMetaDTO, ActorRawDTO, ActorSnapshot
from src.backend.features.combat.dto.pipeline import PipelineContextDTO
from src.backend.features.combat.runtime.engine.ability_service import AbilityService
from src.backend.features.combat.runtime.engine.math_core import MathCore
from src.backend.features.combat.runtime.engine.mechanics_service import MechanicsService
from src.backend.features.combat.runtime.engine.resolver.steps.healing import healing_step
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine


def _actor(skill: str, value: float, profile: str, bonus: float = 0.0) -> ActorSnapshot:
    actor = ActorSnapshot(
        meta=ActorMetaDTO(
            id=1,
            name="Recovery probe",
            type="player" if profile == "player" else "monster",
            team="probe",
            hp=10,
            max_hp=100,
        ),
        raw=ActorRawDTO(
            modifiers={
                "hp": {"base": 100},
                "hp_regen": {"base": 2},
                "magical_damage": {"base": 20},
                "received_healing_bonus": {"base": bonus},
                "vampiric_power": {"base": 0.5},
            },
            rules={"attribute_profile": profile},
        ),
        skills={skill: value},
    )
    StatsEngine.ensure_stats(actor)
    return actor


def _recovery(skill: str, value: float, profile: str, bonus: float = 0.0) -> dict:
    actor = _actor(skill, value, profile, bonus)
    ctx = PipelineContextDTO()
    ctx.stages.calculate_healing = True
    ctx.override_damage = (20, 20)
    ctx.result.source_id = ctx.result.target_id = actor.char_id
    healing_step.run(actor.stats, actor.stats, ctx, ctx.result)
    MechanicsService().apply_interaction_result(ctx, actor, None, ctx.result)
    direct_delta = actor.meta.hp - 10

    actor.meta.hp = 10
    ctx = PipelineContextDTO()
    AbilityService._register_combat_hp_regen(ctx, actor)
    MechanicsService().apply_interaction_result(ctx, actor, None, ctx.result)
    combat_delta = actor.meta.hp - 10
    vitals = CharacterSessionVitalsDTO(
        hp=VitalValueDTO(cur=10, max=100, regen=actor.stats.mods.outside_hp_regen),
        last_update=100,
    )
    CharacterVitalsCalculator.apply_regen(vitals, now=100 + 4 * REGEN_TICK_SECONDS)

    actor.meta.hp = 10
    ctx = PipelineContextDTO()
    AbilityService._apply_prepared_parry_heal(ctx, actor, "probe_prepared_heal", {})
    MechanicsService().apply_interaction_result(ctx, actor, None, ctx.result)
    prepared = {"reported": ctx.result.healing_final, "actual_hp_delta": actor.meta.hp - 10}

    actor.meta.hp = 10
    actor.statuses.effects = [
        ActiveEffectDTO(uid="probe_hot", effect_id="hot_regen_hp", source_id=1, expire_at_exchange=3, impact={"hp": 7})
    ]
    ctx = PipelineContextDTO()
    ctx.flags.mechanics.apply_periodic = True
    MechanicsService().process_turn_start(ctx, actor)
    hot_delta = actor.meta.hp - 10

    actor.meta.hp = 10
    ctx = PipelineContextDTO()
    ctx.flags.damage.vampiric = True
    ctx.result.is_hit = True
    ctx.result.damage_final = 20
    # Force the chance branch while retaining production lifesteal/commit code.
    original_roll = MathCore.roll_chance
    MathCore.roll_chance = staticmethod(lambda chance: (0.0, True))
    try:
        AbilityService._register_vampiric_lifesteal(ctx, actor)
    finally:
        MathCore.roll_chance = staticmethod(original_roll)
    MechanicsService().apply_interaction_result(ctx, actor, None, ctx.result)
    lifesteal = {"reported": ctx.result.healing_final, "actual_hp_delta": actor.meta.hp - 10}

    return {
        "skill": skill,
        "value": value,
        "profile": profile,
        "received_healing_bonus": bonus,
        "combat_hp_regen": actor.stats.mods.combat_hp_regen,
        "outside_hp_regen": actor.stats.mods.outside_hp_regen,
        "direct_heal_hp_delta": direct_delta,
        "combat_regen_hp_delta": combat_delta,
        "outside_four_ticks_hp_delta": vitals.hp.cur - 10,
        "prepared_heal": prepared,
        "hot_tick_hp_delta": hot_delta,
        "lifesteal": lifesteal,
    }


def main() -> None:
    sweep = [
        _recovery(skill, value, profile)
        for skill in ("skill_tactics", "skill_anatomy")
        for profile in ("player", "monster:humanoid", "monster:beast")
        for value in (0.0, 0.25, 0.5, 1.0)
    ]
    controls = [_recovery("skill_anatomy", 1.0, "player", bonus) for bonus in (0.0, 0.25, 0.5, 1.0)]
    print(
        json.dumps(
            {
                "scope": "synthetic fixed raw -> StatsEngine -> recovery -> MechanicsService; no IO",
                "sweep": sweep,
                "received_healing_bonus_control": controls,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
