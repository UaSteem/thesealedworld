"""Incoming healing contracts exercised through production calculation and commit."""

import pytest

from src.backend.features.combat.dto.actor import ActiveEffectDTO, ActorMetaDTO, ActorRawDTO, ActorSnapshot
from src.backend.features.combat.dto.pipeline import PipelineContextDTO
from src.backend.features.combat.runtime.engine.ability_service import AbilityService
from src.backend.features.combat.runtime.engine.math_core import MathCore
from src.backend.features.combat.runtime.engine.mechanics_service import MechanicsService
from src.backend.features.combat.runtime.engine.resolver.steps.healing import healing_step
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine


def actor(actor_id: int, *, bonus: float = 0.5, hp: int = 10) -> ActorSnapshot:
    result = ActorSnapshot(
        meta=ActorMetaDTO(id=actor_id, name=f"Healer {actor_id}", type="player", team=str(actor_id), hp=hp, max_hp=100),
        raw=ActorRawDTO(
            modifiers={
                "hp": {"base": 100},
                "received_healing_bonus": {"base": bonus},
                "hp_regen": {"base": 3.5},
                "vampiric_power": {"base": 0.5},
            }
        ),
    )
    StatsEngine.ensure_stats(result)
    return result


def context(source: ActorSnapshot, target: ActorSnapshot) -> PipelineContextDTO:
    ctx = PipelineContextDTO()
    ctx.result.source_id = source.char_id
    ctx.result.target_id = target.char_id
    return ctx


@pytest.mark.parametrize("self_target", [True, False])
@pytest.mark.parametrize("bonus,expected", [(0.0, 20), (0.5, 30)])
def test_direct_heal_uses_recipient_bonus_and_commits_once(self_target, bonus, expected):
    source = actor(1, bonus=2.0 if not self_target else bonus)
    target = source if self_target else actor(2, bonus=bonus)
    ctx = context(source, target)
    ctx.stages.calculate_healing = True
    ctx.override_damage = (20, 20)

    healing_step.run(source.stats, target.stats, ctx, ctx.result)
    MechanicsService().apply_interaction_result(ctx, source, target, ctx.result)

    assert target.meta.hp == 10 + expected
    if not self_target:
        assert source.meta.hp == 10
    assert ctx.result.healing_final == expected
    assert [(event.target_id, event.value) for event in ctx.result.events if event.type == "HEAL"] == [
        (target.char_id, expected)
    ]
    assert sum(fact.delta for fact in ctx.result.resource_facts if fact.actor_id == target.char_id) == expected


@pytest.mark.parametrize("hp,expected", [(10, 27), (80, 20), (100, 0)])
def test_prepared_parry_heal_scales_before_missing_hp_cap(hp, expected):
    source, target = actor(1, bonus=2), actor(2, hp=hp)
    ctx = context(source, target)

    AbilityService._apply_prepared_parry_heal(ctx, target, "prep_second_breath", {})
    MechanicsService().apply_interaction_result(ctx, source, target, ctx.result)

    assert target.meta.hp == hp + expected
    assert source.meta.hp == 10
    assert ctx.result.healing_final == expected
    assert sum(fact.delta for fact in ctx.result.resource_facts) == expected


@pytest.mark.parametrize(
    "effect_id,params,expected",
    [
        ("restore_hp", {"value": 20}, 30),
        ("shield_blood_heal", {"heal_max_hp_ratio": 0.2}, 30),
    ],
)
@pytest.mark.parametrize("self_target", [True, False])
def test_instant_heal_uses_explicit_recipient_once(effect_id, params, expected, self_target):
    source = actor(1, bonus=0.5 if self_target else 2)
    target = source if self_target else actor(2)
    ctx = context(source, target)
    ctx.result.applied_effects = [{"id": effect_id, "target_id": target.char_id, "params": params}]

    AbilityService._apply_queued_effects(ctx, source, target)
    MechanicsService().apply_interaction_result(ctx, source, target, ctx.result)

    assert target.meta.hp == 10 + expected
    assert ctx.result.healing_final == expected
    if not self_target:
        assert source.meta.hp == 10
    assert sum(fact.delta for fact in ctx.result.resource_facts) == expected
    assert [(event.target_id, event.value) for event in ctx.result.events if event.type == "HEAL"] == [
        (target.char_id, expected)
    ]


def test_hot_uses_current_recipient_bonus_per_tick_without_mutating_base_impact():
    target = actor(1)
    effect = ActiveEffectDTO(uid="hot", effect_id="hot_regen_hp", source_id=2, expire_at_exchange=9, impact={"hp": 10})
    target.statuses.effects.append(effect)

    for bonus, expected in [(0.5, 15), (0.0, 10)]:
        target.raw.modifiers["received_healing_bonus"] = {"base": bonus}
        target.dirty_stats.add("received_healing_bonus")
        before = target.meta.hp
        ctx = context(target, target)
        ctx.flags.mechanics.apply_periodic = True
        MechanicsService().process_turn_start(ctx, target)
        assert target.meta.hp == before + expected
        assert ctx.result.events[0].value == expected
        assert ctx.result.effect_facts[0].value == expected
        assert effect.impact == {"hp": 10}


def test_negative_periodic_damage_is_not_scaled_as_healing():
    target = actor(1, hp=80)
    target.statuses.effects.append(
        ActiveEffectDTO(uid="dot", effect_id="dot_bleed", source_id=2, expire_at_exchange=9, impact={"hp": -10})
    )
    ctx = context(target, target)
    ctx.flags.mechanics.apply_periodic = True
    MechanicsService().process_turn_start(ctx, target)
    assert target.meta.hp == 70
    assert ctx.result.resource_facts[0].delta == -10


def test_lifesteal_scales_recipient_and_commits_once(monkeypatch):
    source, target = actor(1), actor(2, bonus=2)
    ctx = context(source, target)
    ctx.flags.damage.vampiric = True
    ctx.result.is_hit = True
    ctx.result.damage_final = 40
    monkeypatch.setattr(MathCore, "roll_chance", staticmethod(lambda chance: (0.0, True)))

    AbilityService._register_vampiric_lifesteal(ctx, source)
    MechanicsService().apply_interaction_result(ctx, source, target, ctx.result)

    assert source.meta.hp == 40
    assert ctx.result.lifesteal_amount == ctx.result.healing_final == 30
    assert sum(fact.delta for fact in ctx.result.resource_facts if fact.actor_id == source.char_id) == 30


def test_heal_bonus_does_not_multiply_passive_regen_in_same_action():
    source = actor(1)
    ctx = context(source, source)
    ctx.stages.calculate_healing = True
    ctx.override_damage = (20, 20)
    healing_step.run(source.stats, source.stats, ctx, ctx.result)
    AbilityService._register_combat_hp_regen(ctx, source)
    MechanicsService().apply_interaction_result(ctx, source, None, ctx.result)
    assert source.stats.mods.combat_hp_regen == 4
    assert source.meta.hp == 44  # 10 + 20 * 1.5 + 4, not (20 + 4) * 1.5.


def test_direct_heal_commit_clamps_to_max_hp():
    source, target = actor(1, bonus=0), actor(2, hp=90)
    ctx = context(source, target)
    ctx.stages.calculate_healing = True
    ctx.override_damage = (20, 20)
    healing_step.run(source.stats, target.stats, ctx, ctx.result)
    MechanicsService().apply_interaction_result(ctx, source, target, ctx.result)
    assert source.meta.hp == 10
    assert target.meta.hp == 100
    assert sum(fact.delta for fact in ctx.result.resource_facts if fact.actor_id == target.char_id) == 10


def test_critical_heal_scales_before_single_final_integer_conversion():
    source, target = actor(1, bonus=0), actor(2)
    ctx = context(source, target)
    ctx.stages.calculate_healing = True
    ctx.override_damage = (10.9, 10.9)
    ctx.result.is_crit = True
    healing_step.run(source.stats, target.stats, ctx, ctx.result)
    MechanicsService().apply_interaction_result(ctx, source, target, ctx.result)
    assert ctx.result.healing_final == 24  # int(10.9 * 1.5 crit * 1.5 received).
    assert target.meta.hp == 34
    assert ctx.result.events[0].tags == ["CRIT"]
