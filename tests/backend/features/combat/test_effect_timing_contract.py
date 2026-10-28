"""AG04 action boundary, effect windows, and final position contracts."""

import pytest

from src.backend.features.combat.dto import ActiveEffectDTO, ActorSnapshot, CombatActionDTO, PipelineContextDTO
from src.backend.features.combat.dto.pipeline import CombatCheckTraceDTO
from src.backend.features.combat.runtime.engine.mechanics_service import MechanicsService
from src.backend.features.combat.runtime.engine.ranged_position import RangedPositionService
from src.backend.features.combat.runtime.engine.stats_engine import StatsEngine
from src.backend.features.combat.runtime.processors.executor import CombatExecutor
from tests.backend.features.combat.test_exchange_execution_contract import actor, battle, move
from tests.backend.features.combat.test_exchange_execution_contract import (
    deterministic_resolver as deterministic_resolver,
)


@pytest.mark.unit
def test_periodic_ticks_only_inside_personal_window():
    owner = actor("1", "a")
    owner.statuses.effects.append(
        ActiveEffectDTO(
            uid="dot",
            effect_id="dot_bleed",
            source_id="monster",
            active_from_exchange=2,
            expire_at_exchange=4,
            impact={"hp": -7},
        )
    )
    hp = []
    for counter in range(6):
        owner.meta.exchange_counter = counter
        ctx = PipelineContextDTO()
        ctx.flags.mechanics.apply_periodic = True
        MechanicsService().process_turn_start(ctx, owner)
        hp.append(owner.meta.hp)
    assert hp == [1000, 1000, 993, 986, 986, 986]


@pytest.mark.unit
def test_resolved_modifiers_follow_window_after_json_and_cached_stats():
    owner = actor("1", "a")
    owner.raw.modifiers["hp_regen"] = {"base": 1, "source": {}, "temp": {"unrelated": "+2"}}
    owner.statuses.effects.append(
        ActiveEffectDTO(
            uid="future",
            effect_id="future",
            source_id="1",
            active_from_exchange=2,
            expire_at_exchange=4,
            modified_sources={"hp_regen": ["effect-source"]},
            resolved_temp_commands=[
                {
                    "actor_id": "1",
                    "layer": "modifiers",
                    "stat_key": "hp_regen",
                    "source_id": "effect-source",
                    "command": "+10",
                    "base": 1,
                }
            ],
        )
    )
    values = []
    for counter in range(6):
        owner.meta.exchange_counter = counter
        owner = ActorSnapshot.model_validate_json(owner.model_dump_json())
        StatsEngine.ensure_stats(owner)
        values.append(owner.stats.mods.hp_regen)
    assert values == [3, 3, 13, 13, 3, 3]
    assert owner.raw.modifiers["hp_regen"]["temp"] == {"unrelated": "+2"}


@pytest.mark.unit
async def test_one_final_position_for_forced_defender(monkeypatch, deterministic_resolver):
    source, defender = actor("1", "a", dual=True), actor("monster", "b")
    defender.loadout.layout["tactical_style"] = "skill_ranged_combat"
    calls = []

    def roll(**kwargs):
        calls.append(kwargs)
        return "mid"

    monkeypatch.setattr(RangedPositionService, "roll_next_position", staticmethod(roll))
    ctx = battle(source, defender)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster"), is_forced=True)
    )
    assert len(calls) == 1
    assert calls[0]["archer"] is defender
    assert RangedPositionService.current_position(defender) == "mid"
    assert any(
        f["effect_id"] == "ranged_position"
        for t in ctx.pending_result_support_tasks
        for f in t["result"]["effect_facts"]
    )


def patch_feint(monkeypatch, effect_id, *, area=False, own_far=False):
    from src.backend.features.combat.integrations import CombatCatalogIntegrator

    get_entry = CombatCatalogIntegrator.get_feint_catalog_entry
    key = "sword_cross_arc" if area else "second_breath"
    entry = get_entry(key).model_copy(deep=True)
    entry.technical.preparation_effects = []
    entry.technical.effects = [{"id": effect_id, "target_actor": "target", "params": {"duration": 2}}]
    if own_far:
        entry.technical.pipeline_mutations = []
    monkeypatch.setattr(
        CombatCatalogIntegrator,
        "get_feint_catalog_entry",
        staticmethod(lambda name: entry if name == key else get_entry(name)),
    )
    from src.backend.features.combat.runtime.engine.math_core import MathCore

    monkeypatch.setattr(MathCore, "roll_chance", staticmethod(lambda chance: (0.0, chance > 0)))
    return key


@pytest.mark.unit
async def test_aoe_personal_windows_and_exact_ticks_through_own_exchanges(monkeypatch, deterministic_resolver):
    key = patch_feint(monkeypatch, "dot_bleed", area=True)
    source, primary, secondary = actor("1", "a", dual=True), actor("monster", "b"), actor("other", "b")
    source.meta.exchange_counter, primary.meta.exchange_counter, secondary.meta.exchange_counter = 4, 9, 2
    ctx = battle(source, primary, secondary)
    executor = CombatExecutor()
    await executor._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster", key), is_forced=True)
    )
    for target, start in ((primary, 10), (secondary, 2)):
        effect = next(e for e in target.statuses.effects if e.effect_id == "dot_bleed")
        assert (effect.active_from_exchange, effect.expire_at_exchange) == (start, start + 2)
        assert target.meta.exchange_counter == start
    # Roundtrip entire battle snapshots, and count actual turn-start resource facts.
    ctx.actors = {k: ActorSnapshot.model_validate_json(v.model_dump_json()) for k, v in ctx.actors.items()}
    for target_id in ("monster", "other"):
        ticks = []
        for _ in range(3):
            before = len(ctx.pending_result_support_tasks)
            await executor._handle_exchange(
                ctx, CombatActionDTO(action_type="exchange", move=move(target_id, "1"), is_forced=True)
            )
            ticks.append(
                sum(
                    1
                    for task in ctx.pending_result_support_tasks[before:]
                    for fact in task["result"]["resource_facts"]
                    if fact["actor_id"] == target_id and fact["reason"] == "effect_tick"
                )
            )
        assert ticks == [1, 1, 0]


@pytest.mark.unit
async def test_future_regen_modifiers_do_not_affect_current_finalize(monkeypatch, deterministic_resolver):
    from tests.backend.features.combat.test_exchange_regen_contract import regen_results, regenerating

    source, target = regenerating("1", "a", dual=True), regenerating("monster", "b")
    target.statuses.effects.append(
        ActiveEffectDTO(
            uid="future",
            effect_id="future",
            source_id="1",
            active_from_exchange=1,
            expire_at_exchange=2,
            modified_sources={"hp_regen": ["hp-effect"], "stamina_regen": ["st-effect"]},
            resolved_temp_commands=[
                {
                    "actor_id": "monster",
                    "layer": "modifiers",
                    "stat_key": key,
                    "source_id": source_id,
                    "command": "+10",
                    "base": 0,
                }
                for key, source_id in [("hp_regen", "hp-effect"), ("stamina_regen", "st-effect")]
            ],
        )
    )
    StatsEngine.ensure_stats(target)
    ctx = battle(source, target)
    executor = CombatExecutor()
    await executor._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster"), is_forced=True)
    )
    first = regen_results(ctx)[-1]
    assert [(f["resource"], f["delta"]) for f in first["resource_facts"] if f["actor_id"] == "monster"] == [
        ("hp", 7),
        ("stamina", 3),
    ]
    restored = ActorSnapshot.model_validate_json(target.model_dump_json())
    assert restored.stats is not None
    ctx.actors["monster"] = restored
    await executor._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("monster", "1"), is_forced=True)
    )
    second = regen_results(ctx)[-1]
    assert [(f["resource"], f["delta"]) for f in second["resource_facts"] if f["actor_id"] == "monster"] == [
        ("hp", 17),
        ("stamina", 13),
    ]
    StatsEngine.ensure_stats(restored)
    assert restored.stats.mods.hp_regen == 7
    assert restored.stats.mods.stamina_regen == 3


@pytest.mark.unit
@pytest.mark.parametrize("area", [False, True])
async def test_force_close_wins_final_roll_and_does_not_replace_current_position_in_waves(
    monkeypatch, deterministic_resolver, area
):
    from src.backend.features.combat.runtime.engine.pipeline import CombatPipeline

    key = patch_feint(monkeypatch, "force_ranged_close", area=area)
    source, primary, secondary = actor("1", "a", dual=True), actor("monster", "b", dual=True), actor("other", "b")
    for target in (primary, secondary):
        target.loadout.layout["tactical_style"] = "skill_ranged_combat"
        target.statuses.effects.append(
            ActiveEffectDTO(
                uid="old-" + str(target.char_id),
                effect_id="ranged_position",
                source_id=target.char_id,
                active_from_exchange=0,
                expire_at_exchange=1,
                params={"position": "mid"},
            )
        )
    calculate = CombatPipeline.calculate
    observed = []

    async def observe(self, source, target, move, **kwargs):
        result = await calculate(self, source, target, move, **kwargs)
        if result.action_facts["execution"]["origin"] == "offhand":
            observed.append(RangedPositionService.current_position(target))
        if result.source_id == "monster":
            result.action_facts.update(next_ranged_position_override="far", next_ranged_position_min="far")
        return result

    monkeypatch.setattr(CombatPipeline, "calculate", observe)
    calls = []
    monkeypatch.setattr(
        RangedPositionService, "roll_next_position", staticmethod(lambda **kw: calls.append(kw) or "far")
    )
    ctx = battle(source, primary, secondary)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster", key), partner_move=move("monster", "1"))
    )
    assert observed and all(position == "mid" for position in observed)
    assert not calls
    for target in (primary, secondary) if area else (primary,):
        assert RangedPositionService.current_position(target) == "close"
        effect = next(e for e in target.statuses.effects if e.effect_id == "ranged_position")
        assert effect.active_from_exchange == target.meta.exchange_counter
        assert effect.expire_at_exchange == target.meta.exchange_counter + 1
    final_tasks = [
        task
        for task in ctx.pending_result_support_tasks
        if "execution" not in task["result"]["action_facts"] and task["result"]["effect_facts"]
    ]
    assert final_tasks
    assert any(
        f["effect_id"] == "ranged_position" and "close" in f["tags"]
        for task in final_tasks
        for f in task["result"]["effect_facts"]
    )
    assert any(
        f["style"] == "skill_ranged_combat" and f["after"] == "close"
        for task in final_tasks
        for f in task["result"]["tactical_transitions"]
    )


@pytest.mark.unit
async def test_force_close_unidirectional_does_not_increment_or_roll(monkeypatch, deterministic_resolver):
    from src.backend.features.combat.dto import CombatMoveDTO, InstantPayload
    from src.backend.features.combat.runtime.engine.resolver import CombatResolver

    resolve = CombatResolver.resolve_exchange

    def add_close(source, target, ctx):
        resolve(source, target, ctx)
        ctx.result.applied_effects.append({"id": "force_ranged_close", "target_id": ctx.result.target_id})

    monkeypatch.setattr(CombatResolver, "resolve_exchange", staticmethod(add_close))
    monkeypatch.setattr(
        RangedPositionService, "roll_next_position", staticmethod(lambda **kw: pytest.fail("instant cannot roll"))
    )
    source, target = actor("1", "a"), actor("monster", "b")
    source.meta.en = 100
    source.meta.tokens.update(tempo=99, pressure=99, gift=99, hit=99)
    target.meta.exchange_counter = 4
    target.loadout.layout["tactical_style"] = "skill_ranged_combat"
    ctx = battle(source, target)
    await CombatExecutor()._handle_unidirectional(
        ctx,
        CombatActionDTO(
            action_type="instant",
            move=CombatMoveDTO(
                move_id="instant",
                char_id="1",
                strategy="instant",
                targets=["monster"],
                payload=InstantPayload(ability_id="basic_splinter_strike", target_id="monster"),
            ),
        ),
    )
    assert target.meta.exchange_counter == 4
    assert RangedPositionService.current_position(target) == "close"
    transitions = [fact for task in ctx.pending_result_support_tasks for fact in task["result"]["tactical_transitions"]]
    assert len(transitions) == 1
    assert (transitions[0]["before"], transitions[0]["after"], transitions[0]["source_action_id"]) == (
        "far",
        "close",
        "basic_splinter_strike",
    )
    assert not any(
        f["reason"] == "combat_regen"
        for task in ctx.pending_result_support_tasks
        for f in task["result"]["resource_facts"]
    )


@pytest.mark.unit
async def test_all_wave_pressure_and_own_primary_facts(monkeypatch, deterministic_resolver):
    from src.backend.features.combat.runtime.engine.pipeline import CombatPipeline

    source, target = actor("1", "a", dual=True), actor("monster", "b", dual=True)
    source.loadout.layout["tactical_style"] = "skill_ranged_combat"
    calculate = CombatPipeline.calculate

    async def inject(self, source, target, move, **kwargs):
        result = await calculate(self, source, target, move, **kwargs)
        result.action_facts["ranged_far_weight_bonus"] = 0.7 if move.origin == "primary" else -0.8
        if move.origin == "primary" and result.source_id == "1":
            result.chain_events.trigger_counter_attack = True
        if result.target_id == "1":
            result.damage_final = 10
            result.checks.append(CombatCheckTraceDTO(stage="ranged_position_defense", chance=0, roll=1, passed=False))
        return result

    monkeypatch.setattr(CombatPipeline, "calculate", inject)
    calls = []
    monkeypatch.setattr(
        RangedPositionService, "roll_next_position", staticmethod(lambda **kw: calls.append(kw) or "mid")
    )
    ctx = battle(source, target)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster"), partner_move=move("monster", "1"))
    )
    assert len(calls) == 1
    assert calls[0]["damage_taken"] == 40
    assert calls[0]["melee_pressure"] == 4
    assert calls[0]["action_facts"]["ranged_far_weight_bonus"] == 0.7


@pytest.mark.unit
def test_foreign_recipient_commands_both_layers_and_legacy_capture():
    owner, recipient = actor("1", "a"), actor("monster", "b")
    recipient.raw.attributes["strength"] = {"base": 3, "source": {}, "temp": {"foreign-attr": "+5", "item": "+2"}}
    recipient.raw.modifiers["hp_regen"] = {"base": 1, "source": {}, "temp": {"foreign-mod": "+9"}}
    owner.statuses.effects.append(
        ActiveEffectDTO(
            uid="foreign",
            effect_id="foreign",
            source_id="1",
            active_from_exchange=2,
            expire_at_exchange=3,
            modified_sources={"strength": ["foreign-attr"], "hp_regen": ["foreign-mod"]},
        )
    )
    StatsEngine.ensure_stats(owner)  # Must not freeze [] before foreign recipient is available.
    assert owner.statuses.effects[0].resolved_temp_commands is None
    StatsEngine.sync_effect_modifiers([owner, recipient])
    assert recipient.raw.attributes["strength"]["temp"] == {"item": "+2"}
    owner, recipient = [ActorSnapshot.model_validate_json(a.model_dump_json()) for a in (owner, recipient)]
    owner.meta.exchange_counter = 2
    StatsEngine.sync_effect_modifiers([owner, recipient])
    assert recipient.raw.attributes["strength"]["temp"]["foreign-attr"] == "+5"
    assert recipient.raw.modifiers["hp_regen"]["temp"]["foreign-mod"] == "+9"
    owner.meta.exchange_counter = 3
    StatsEngine.sync_effect_modifiers([owner, recipient])
    assert recipient.raw.attributes["strength"]["temp"] == {"item": "+2"}
    assert recipient.raw.modifiers["hp_regen"]["temp"] == {}


@pytest.mark.unit
async def test_queued_modifiers_on_secondary_are_absent_until_action_end(monkeypatch, deterministic_resolver):
    from src.backend.features.combat.runtime.engine.pipeline import CombatPipeline

    key = patch_feint(monkeypatch, "buff_armor", area=True)
    source, primary, secondary = actor("1", "a", dual=True), actor("monster", "b"), actor("other", "b")
    calculate = CombatPipeline.calculate
    seen = []
    ctx = battle(source, primary, secondary)

    async def observe(self, source, target, move, **kwargs):
        if move.origin == "offhand":
            StatsEngine.ensure_stats(secondary)
            seen.append((list(secondary.statuses.effects), secondary.stats.mods.armor))
        return await calculate(self, source, target, move, **kwargs)

    monkeypatch.setattr(CombatPipeline, "calculate", observe)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster", key), is_forced=True)
    )
    assert seen == [([], 0)]
    StatsEngine.ensure_stats(secondary)
    assert secondary.stats.mods.armor == 1
    assert secondary.meta.exchange_counter == 0


@pytest.mark.unit
async def test_dead_ranged_main_neither_rolls_nor_receives_close(monkeypatch, deterministic_resolver):
    from src.backend.features.combat.runtime.engine.pipeline import CombatPipeline

    key = patch_feint(monkeypatch, "force_ranged_close")
    source, target = actor("1", "a"), actor("monster", "b")
    target.loadout.layout["tactical_style"] = "skill_ranged_combat"
    calculate = CombatPipeline.calculate

    async def lethal(self, source, target, move, **kwargs):
        result = await calculate(self, source, target, move, **kwargs)
        result.damage_final = 5000
        return result

    monkeypatch.setattr(CombatPipeline, "calculate", lethal)
    monkeypatch.setattr(
        RangedPositionService, "roll_next_position", staticmethod(lambda **kw: pytest.fail("dead actor roll"))
    )
    ctx = battle(source, target)
    await CombatExecutor()._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster", key), is_forced=True)
    )
    assert not target.is_alive
    assert not target.statuses.effects
    assert not any(
        f["effect_id"] == "force_ranged_close"
        for task in ctx.pending_result_support_tasks
        for f in task["result"]["effect_facts"]
    )


@pytest.mark.unit
@pytest.mark.parametrize("secondary_target", [False, True])
async def test_queued_regen_commands_wait_for_next_own_exchange_after_roundtrip(
    monkeypatch, deterministic_resolver, secondary_target
):
    from dataclasses import replace

    from src.backend.features.combat.integrations import CombatCatalogIntegrator
    from src.backend.features.combat.runtime.engine import modifier_application_service as modifiers
    from src.backend.features.game_catalog.combat.resources.common.modifier_applications import ModifierApplicationDTO
    from tests.backend.features.combat.test_exchange_regen_contract import regen_results, regenerating

    key = patch_feint(monkeypatch, "buff_armor", area=secondary_target)
    effect_entry = CombatCatalogIntegrator.get_effect_catalog_entry
    entry = effect_entry("buff_armor").model_copy(deep=True)
    entry.technical.modifier_applications = [
        ModifierApplicationDTO(modifier_id=key, value_override=10) for key in ("hp_regen_add", "test_stamina_regen_add")
    ]
    get_contract = modifiers.get_modifier_contract
    stamina = replace(get_contract("hp_regen_add"), id="test_stamina_regen_add", target_field="stamina_regen")
    monkeypatch.setattr(
        modifiers,
        "get_modifier_contract",
        lambda name: stamina if name == "test_stamina_regen_add" else get_contract(name),
    )
    monkeypatch.setattr(
        CombatCatalogIntegrator,
        "get_effect_catalog_entry",
        staticmethod(lambda name: entry if name == "buff_armor" else effect_entry(name)),
    )
    source, primary, secondary = (
        regenerating("1", "a", dual=True),
        regenerating("monster", "b"),
        regenerating("other", "b"),
    )
    ctx = battle(source, primary, secondary)
    executor = CombatExecutor()
    await executor._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move("1", "monster", key), is_forced=True)
    )
    first = regen_results(ctx)[-1]
    assert [(f["resource"], f["delta"]) for f in first["resource_facts"] if f["actor_id"] == "monster"] == [
        ("hp", 7),
        ("stamina", 3),
    ]
    recipient_id = "other" if secondary_target else "monster"
    ctx.actors = {key: ActorSnapshot.model_validate_json(value.model_dump_json()) for key, value in ctx.actors.items()}
    recipient = ctx.actors[recipient_id]
    assert recipient.statuses.effects[0].resolved_temp_commands
    await executor._handle_exchange(
        ctx, CombatActionDTO(action_type="exchange", move=move(recipient_id, "1"), is_forced=True)
    )
    second = regen_results(ctx)[-1]
    assert [(f["resource"], f["delta"]) for f in second["resource_facts"] if f["actor_id"] == recipient_id] == [
        ("hp", 17),
        ("stamina", 13),
    ]


@pytest.mark.unit
def test_blocked_queued_exclusive_preserves_immediate_loop_application():
    from src.backend.features.combat.runtime.engine.ability_service import AbilityService

    source, target = actor("1", "a"), actor("monster", "b")
    source.statuses.effects.append(
        ActiveEffectDTO(uid="existing", effect_id="prep_counter_on_parry", source_id="1", expire_at_exchange=9)
    )
    ctx = PipelineContextDTO()
    ctx.result.source_id, ctx.result.target_id = "1", "monster"
    ctx.flags.meta.defer_queued_statuses = True
    AbilityService._append_runtime_effect(source, "prep_dual_blade_loop_counter", ctx=ctx)
    ctx.result.applied_effects.append({"id": "prep_perfect_riposte", "target_id": "1"})
    AbilityService._apply_queued_effects(ctx, source, target)
    assert len(ctx.result.status_applications) == 1
    assert ctx.result.status_applications[0].effect_id == "prep_dual_blade_loop_counter"
    assert not ctx.result.status_applications[0].at_action_end
