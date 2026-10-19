"""Only exchanges advance periodic effects; instant actions execute their own work."""

import pytest

from src.backend.features.combat.dto import (
    ActiveEffectDTO,
    CombatActionDTO,
    CombatMoveDTO,
    InstantPayload,
    InteractionResultDTO,
)
from src.backend.features.combat.dto.pipeline import CombatResourceApplicationDTO
from src.backend.features.combat.runtime.engine.pipeline import CombatPipeline
from src.backend.features.combat.runtime.processors.executor import CombatExecutor
from tests.backend.features.combat.test_exchange_execution_contract import actor, battle, move
from tests.backend.features.combat.test_exchange_execution_contract import (
    deterministic_resolver as deterministic_resolver,
)


@pytest.mark.unit
async def test_repeated_instants_do_not_tick_but_next_exchange_ticks_both_owners(deterministic_resolver):
    source, target = actor("1", "a", dual=True), actor("monster", "b")
    source.meta.en = source.meta.max_en = 100
    source.meta.tokens.update(tempo=99, pressure=99, gift=99, hit=99)
    for participant in (source, target):
        participant.meta.en = participant.meta.max_en = 100
        participant.statuses.effects.append(
            ActiveEffectDTO(
                uid=f"bleed-{participant.char_id}",
                effect_id="dot_bleed",
                source_id=target.char_id,
                expire_at_exchange=3,
                impact={"hp": -7, "en": -2},
            )
        )
    ctx = battle(source, target)
    executor = CombatExecutor()
    for number in range(3):
        await executor._process_single_action(
            ctx,
            CombatActionDTO(
                action_type="instant",
                move=CombatMoveDTO(
                    move_id=f"instant-{number}",
                    char_id=source.char_id,
                    strategy="instant",
                    targets=[target.char_id],
                    payload=InstantPayload(ability_id="basic_splinter_strike", target_id=target.char_id),
                ),
            ),
        )
    assert source.meta.hp == 1000
    assert target.meta.hp < 1000  # The instant's own attack still executes.
    assert source.meta.exchange_counter == target.meta.exchange_counter == ctx.meta.step_counter == 0
    assert not any(
        fact["reason"] == "effect_tick"
        for task in ctx.pending_result_support_tasks
        for fact in task["result"]["resource_facts"]
    )
    assert not any(entry["kind"] == "effect_tick" for entry in ctx.pending_logs)

    first_exchange = len(ctx.pending_result_support_tasks)
    await executor._process_single_action(
        ctx,
        CombatActionDTO(action_type="exchange", move=move("1", "monster"), is_forced=True),
    )
    ticks = [
        (fact["actor_id"], fact["resource"], fact["delta"])
        for task in ctx.pending_result_support_tasks[first_exchange:]
        for fact in task["result"]["resource_facts"]
        if fact["reason"] == "effect_tick"
    ]
    assert ticks == [("1", "hp", -7), ("1", "en", -2), ("monster", "hp", -7), ("monster", "en", -2)]
    assert source.meta.hp == 993
    assert source.meta.exchange_counter == target.meta.exchange_counter == ctx.meta.step_counter == 1


@pytest.mark.unit
@pytest.mark.parametrize("action_type", ["item", "system"])
async def test_other_one_way_actions_apply_own_effect_without_lethal_periodic_tick(monkeypatch, action_type):
    source, target = actor("1", "a"), actor("monster", "b")
    source.meta.hp = 1
    source.statuses.effects.append(
        ActiveEffectDTO(
            uid="lethal-bleed", effect_id="dot_bleed", source_id="monster", expire_at_exchange=3, impact={"hp": -7}
        )
    )

    async def calculate(self, source, target, move, **kwargs):
        return InteractionResultDTO(
            source_id=source.char_id,
            target_id=target.char_id,
            resource_applications=[
                CombatResourceApplicationDTO(
                    actor_id=source.char_id, owner="source", resource="hp", reason="action_effect", value="+5"
                )
            ],
        )

    monkeypatch.setattr(CombatPipeline, "calculate", calculate)
    ctx = battle(source, target)
    await CombatExecutor()._process_single_action(
        ctx,
        CombatActionDTO(
            action_type=action_type,
            move=CombatMoveDTO(
                move_id="one-way",
                char_id="1",
                strategy=action_type,
                targets=["monster"],
                payload={"target_id": "monster"},
            ),
        ),
    )
    assert source.meta.hp == 6
    assert source.is_alive
    assert source.meta.exchange_counter == target.meta.exchange_counter == ctx.meta.step_counter == 0
    assert [
        fact["reason"] for task in ctx.pending_result_support_tasks for fact in task["result"]["resource_facts"]
    ] == ["action_effect"]
