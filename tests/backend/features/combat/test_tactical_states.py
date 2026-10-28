from unittest.mock import patch

import pytest

from src.backend.features.combat.dto.actor import ActorStats
from src.backend.features.combat.dto.pipeline import InteractionResultDTO, PipelineContextDTO
from src.backend.features.combat.runtime.engine.tactical_state import TacticalStateService
from tests.backend.features.combat.test_exchange_execution_contract import actor, battle, move
from tests.backend.features.combat.test_exchange_execution_contract import (
    deterministic_resolver as deterministic_resolver,
)


def combatant(actor_id, style, initiative=0):
    a = actor(actor_id, "a" if actor_id == "a" else "b")
    a.loadout.layout["tactical_style"] = style
    a.stats = ActorStats()
    setattr(a.stats.skills, style, 1.0)
    a.stats.mods.initiative = initiative
    return a


@pytest.mark.parametrize("own,enemy", [(0, 0), (-50, -50), (-50, 50), (50, -50), (1e9, -1e9)])
def test_probabilities_bounded_and_entry_loss_distinct(own, enemy):
    entry, loss = TacticalStateService.probabilities(own, enemy)
    assert 0.05 <= entry <= 0.75
    assert 0.05 <= loss <= 0.75
    assert entry + loss == pytest.approx(0.5)


def test_frozen_decisions_next_exchange_forced_defender_and_no_secondary_roll():
    a = combatant("a", "skill_two_handed")
    b = combatant("b", "skill_dual_wield")
    primary = InteractionResultDTO(source_id="a", target_id="b")
    secondary = InteractionResultDTO(source_id="a", target_id="b", action_facts={"execution": {"origin": "offhand"}})
    final = InteractionResultDTO()
    with patch.object(TacticalStateService, "roll", return_value=0.0) as rolls:
        TacticalStateService.update_after_exchange(
            [(a, b, primary), (a, b, secondary)], participants=(a, b), final_result=final, seed="battle"
        )
    assert rolls.call_count == 2
    assert TacticalStateService.current_state(a) == "normal"
    a.meta.exchange_counter += 1
    b.meta.exchange_counter += 1
    assert TacticalStateService.current_state(a) == TacticalStateService.current_state(b) == "advantage"
    assert len(final.tactical_transitions) == 2


def test_dead_and_impossible_exchange_dont_create_advantage():
    a = combatant("a", "skill_two_handed")
    b = combatant("b", "skill_dual_wield")
    a.meta.hp = 0
    final = InteractionResultDTO()
    TacticalStateService.update_after_exchange(
        [(a, b, InteractionResultDTO(skip_reason="DEAD"))], participants=(a, b), final_result=final, seed="x"
    )
    assert not final.tactical_transitions


def test_context_bonus_does_not_accumulate_or_modify_actor():
    a = combatant("a", "skill_dual_wield")
    TacticalStateService.set_next_state(a, "advantage", InteractionResultDTO())
    a.meta.exchange_counter += 1
    for hand in ("main_hand", "off_hand"):
        ctx = PipelineContextDTO()
        ctx.flags.meta.source_type = hand
        TacticalStateService.apply_context(ctx, a, None)
        assert ctx.mods.tactical_crit_bonus == 0.05
    assert a.stats.mods.crit_chance == 0


@pytest.mark.parametrize("hand", ["main_hand", "off_hand"])
def test_actual_crit_chance_adds_state_bonus_after_weapon_mastery(hand):
    from src.backend.features.combat.runtime.engine.math_core import MathCore
    from src.backend.features.combat.runtime.engine.resolver.steps.crit import CritStep

    a = combatant("a", "skill_dual_wield")
    b = combatant("b", "skill_two_handed")
    TacticalStateService.set_next_state(a, "advantage", InteractionResultDTO())
    a.meta.exchange_counter += 1
    setattr(a.stats.mods, f"{hand}_crit_chance", 0.10)
    setattr(a.stats.mods, f"{hand}_crit_cap", 1.0)
    a.stats.skills.skill_swords = 3
    ctx = PipelineContextDTO()
    ctx.flags.meta.source_type = hand
    ctx.flags.meta.weapon_class = "swords"
    TacticalStateService.apply_context(ctx, a, b)
    with patch.object(MathCore, "roll_chance", return_value=(0.9, False)) as roll:
        CritStep().run(a.stats, b.stats, ctx, ctx.result)
    assert roll.call_args.args[0] == pytest.approx(0.45)


def test_actual_parry_and_own_anti_dodge_calculations():
    from src.backend.features.combat.runtime.engine.math_core import MathCore
    from src.backend.features.combat.runtime.engine.resolver.steps.evasion import EvasionStep
    from src.backend.features.combat.runtime.engine.resolver.steps.parry import ParryStep

    a = combatant("a", "skill_shield_mastery")
    b = combatant("b", "skill_two_handed")
    for owner in (a, b):
        TacticalStateService.set_next_state(owner, "advantage", InteractionResultDTO())
        owner.meta.exchange_counter += 1
    b.stats.mods.evasion = 0.3
    b.stats.mods.dodge_cap = 1
    b.stats.mods.parry_cap = 1
    ctx = PipelineContextDTO()
    TacticalStateService.apply_context(ctx, a, b)
    with patch.object(MathCore, "roll_chance", return_value=(0.9, False)) as roll:
        EvasionStep().run(a.stats, b.stats, ctx, ctx.result)
        assert roll.call_args.args[0] == pytest.approx(0.25)
        ParryStep().run(a.stats, b.stats, ctx, ctx.result)
        assert roll.call_args.args[0] == pytest.approx(0.05)
    assert b.stats.mods.evasion == 0.3
    assert a.stats.mods.anti_dodge_chance == 0


def test_guaranteed_dislodge_beats_protect_and_entry_order_independent():
    for reverse in (False, True):
        a = combatant("a", "skill_two_handed")
        b = combatant("b", "skill_shield_mastery")
        TacticalStateService.set_next_state(a, "advantage", InteractionResultDTO())
        a.meta.exchange_counter += 1
        own = InteractionResultDTO(
            source_id="a", target_id="b", action_facts={"tactical_protect": True, "tactical_force_advantage": True}
        )
        hostile = InteractionResultDTO(
            source_id="b",
            target_id="a",
            is_hit=True,
            action_facts={"tactical_dislodge": True, "id": "aggressive_defense", "role": "feint"},
        )
        pairs = [(a, b, own), (b, a, hostile)]
        final = InteractionResultDTO()
        TacticalStateService.update_after_exchange(
            list(reversed(pairs)) if reverse else pairs, participants=(a, b), final_result=final, seed="x"
        )
        fact = next(f for f in final.tactical_transitions if str(f.actor_id) == "a")
        assert (fact.before, fact.after, fact.reason, fact.source_feint_id) == (
            "advantage",
            "normal",
            "feint_dislodge",
            "aggressive_defense",
        )


def test_secondary_aoe_target_not_owner_and_state_survives_serialization():
    from src.backend.features.combat.dto.actor import ActorSnapshot

    a = combatant("a", "skill_dual_wield")
    b = combatant("b", "skill_shield_mastery")
    c = combatant("c", "skill_two_handed", 1e9)
    primary = InteractionResultDTO(source_id="a", target_id="b")
    secondary = InteractionResultDTO(source_id="a", target_id="c", action_facts={"execution": {"origin": "secondary"}})
    final = InteractionResultDTO()
    with patch.object(TacticalStateService, "roll", return_value=0) as roll:
        TacticalStateService.update_after_exchange(
            [(a, b, primary), (a, c, secondary)], participants=(a, b), final_result=final, seed="x"
        )
        assert roll.call_count == 2
    assert not c.statuses.effects
    restored = ActorSnapshot.model_validate_json(a.model_dump_json())
    restored.meta.exchange_counter += 1
    assert TacticalStateService.current_state(restored) == "advantage"
    restored.loadout.layout["tactical_style"] = "skill_shield_mastery"
    assert TacticalStateService.current_state(restored) == "normal"


def test_tactical_random_is_reproducible_and_does_not_touch_global_rng():
    import random

    a = combatant("a", "skill_two_handed")
    state = random.getstate()
    assert TacticalStateService.roll("battle", a) == TacticalStateService.roll("battle", a)
    assert state == random.getstate()
    assert TacticalStateService.roll("battle2", a) != TacticalStateService.roll("battle", a)


@pytest.mark.parametrize("mastery,bonus", [(0, 0), (0.5, 0.025), (1, 0.05)])
@pytest.mark.parametrize(
    "style,field",
    [
        ("skill_two_handed", "tactical_parry_bonus"),
        ("skill_shield_mastery", "tactical_anti_dodge_bonus"),
        ("skill_dual_wield", "tactical_crit_bonus"),
    ],
)
def test_style_mastery_scales_bonus_independently_of_weapon_mastery(mastery, bonus, style, field):
    a = combatant("a", style)
    setattr(a.stats.skills, style, mastery)
    a.stats.skills.skill_swords = 100
    TacticalStateService.set_next_state(a, "advantage", InteractionResultDTO())
    a.meta.exchange_counter += 1
    ctx = PipelineContextDTO()
    TacticalStateService.apply_context(ctx, a, a)
    assert getattr(ctx.mods, field) == pytest.approx(bonus)


@pytest.mark.unit
async def test_real_executor_rolls_once_per_owner_after_offhand_and_applies_only_next_exchange(
    monkeypatch, deterministic_resolver
):
    from src.backend.features.combat.dto import CombatActionDTO
    from src.backend.features.combat.runtime.processors.executor import CombatExecutor

    a, b = actor("a", "a", dual=True), actor("b", "b", dual=True)
    ctx = battle(a, b)
    executor = CombatExecutor()
    with patch.object(TacticalStateService, "roll", return_value=0) as rolls:
        await executor._handle_exchange(
            ctx, CombatActionDTO(action_type="exchange", move=move("a", "b"), partner_move=move("b", "a"))
        )
        assert rolls.call_count == 2
    results = [
        task["result"] for task in ctx.pending_result_support_tasks if "execution" in task["result"]["action_facts"]
    ]
    assert [r["action_facts"]["execution"]["origin"] for r in results] == ["primary", "primary", "offhand", "offhand"]
    assert TacticalStateService.current_state(a) == TacticalStateService.current_state(b) == "advantage"
    facts = [fact for task in ctx.pending_result_support_tasks for fact in task["result"]["tactical_transitions"]]
    assert len(facts) == 2
    # The guaranteed zero loss roll happens only after that advantageous exchange
    # has actually been used, with no extra roll on either offhand.
    with patch.object(TacticalStateService, "roll", return_value=0) as rolls:
        await executor._handle_exchange(
            ctx, CombatActionDTO(action_type="exchange", move=move("a", "b"), partner_move=move("b", "a"))
        )
        assert rolls.call_count == 2
    assert TacticalStateService.current_state(a) == TacticalStateService.current_state(b) == "normal"


def test_forced_ranged_transition_keeps_originating_feint():
    from src.backend.features.combat.runtime.engine.ranged_position import RangedPositionService

    a = combatant("a", "skill_ranged_combat")
    b = combatant("b", "skill_two_handed")
    final = InteractionResultDTO()
    RangedPositionService.set_next_position(
        a, "close", final, forced_close=True, source_action_id="press", source_feint_id="press"
    )
    TacticalStateService.update_after_exchange(
        [(b, a, InteractionResultDTO(source_id="b", target_id="a"))],
        participants=(a, b),
        final_result=final,
        seed="battle",
    )
    fact = next(f for f in final.tactical_transitions if str(f.actor_id) == "a")
    assert (fact.before, fact.after, fact.source_feint_id) == ("far", "close", "press")


@pytest.mark.unit
def test_shield_advantage_reduces_archer_special_defense_actual_roll():
    from src.backend.features.combat.runtime.engine.math_core import MathCore
    from src.backend.features.combat.runtime.engine.ranged_position import RangedPositionService
    from src.backend.features.combat.runtime.engine.resolver.steps.ranged_position_defense import (
        RangedPositionDefenseStep,
    )

    source = combatant("a", "skill_shield_mastery")
    target = combatant("b", "skill_ranged_combat")
    target.stats.skills.skill_ranged_combat = 0
    target.stats.mods.evasion = 0.30
    TacticalStateService.set_next_state(source, "advantage", InteractionResultDTO())
    source.meta.exchange_counter += 1
    ctx = PipelineContextDTO()
    ctx.flags.meta.weapon_class = "swords"
    RangedPositionService.apply_target_context(ctx, target)
    TacticalStateService.apply_context(ctx, source, target)
    with patch.object(MathCore, "roll_chance", return_value=(0.99, False)) as roll:
        RangedPositionDefenseStep().run(source.stats, target.stats, ctx, ctx.result)
    assert roll.call_args.args[0] == pytest.approx((0.30 - 0.05) * 0.75)
    assert target.stats.mods.evasion == 0.30
    assert source.stats.mods.anti_dodge_chance == 0


@pytest.mark.unit
def test_public_combat_effect_projection_preserves_tactical_state_params():
    from src.backend.features.combat.services.view_service import CombatViewService
    from src.shared.schemas.combat import CombatEffectBadgeDTO

    owner = combatant("a", "skill_dual_wield")
    TacticalStateService.set_next_state(owner, "advantage", InteractionResultDTO())
    owner.meta.exchange_counter += 1
    badges = CombatViewService._effects(owner.statuses.model_dump(mode="json"))
    assert len(badges) == 1
    public = CombatEffectBadgeDTO.model_validate_json(badges[0].model_dump_json())
    assert public.effect_id == "tactical_state"
    assert public.params == {"style": "skill_dual_wield", "state": "advantage"}
