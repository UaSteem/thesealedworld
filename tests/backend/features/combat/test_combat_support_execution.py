"""Support skills cross real AC input, lifecycle snapshot, pipeline and commit."""

from types import SimpleNamespace

import pytest

from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
from src.backend.features.character.schemas.session import CharacterSessionAttributesDTO
from src.backend.features.combat.dto import (
    ActorSnapshot,
    BattleContext,
    BattleMeta,
    CombatActionDTO,
    CombatMoveDTO,
    ExchangePayload,
    InstantPayload,
    PipelineContextDTO,
)
from src.backend.features.combat.runtime.engine.math_core import MathCore
from src.backend.features.combat.runtime.engine.mechanics_service import MechanicsService
from src.backend.features.combat.runtime.engine.pipeline import CombatPipeline
from src.backend.features.combat.runtime.engine.resolver import CombatResolver
from src.backend.features.combat.runtime.processors.executor import CombatExecutor
from src.backend.features.combat.services.lifecycle_service import CombatLifecycleService


def built_actor(actor_id, *, anatomy=0.0, tactics=0.0, attributes=None, light_armor=False):
    """Use production player AC -> commitment -> lifecycle mapping, with no stores."""
    attrs = dict.fromkeys(CharacterSessionAttributesDTO.model_fields, 0)
    attrs.update(attributes or {})
    items = {"layout": {"equipment": {}}, "by_id": {"spellbook": {"abilities": ["heal"]}}}
    if light_armor:
        items["layout"]["equipment"]["chest_armor"] = "light-chest"
        items["by_id"]["light-chest"] = {"item_type": "armor", "skill_key": "skill_light_armor"}
    active = {
        "char_id": actor_id,
        "bio": {"name": f"Actor {actor_id}"},
        "attributes": attrs,
        "skills": {"skill_anatomy": {"value": anatomy}, "skill_tactics": {"value": tactics}},
        "items": items,
        "vitals": {
            "hp": {"cur": 10, "max": 1000},
            "energy": {"cur": 100, "max": 100},
            "stamina": {"cur": 100, "max": 100},
        },
    }
    snapshot = CharacterCombatActorInputBuilder().build_snapshot(active)
    # _build_actor_doc is a pure production mapper; the store is never accessed.
    payload = CombatLifecycleService(store=SimpleNamespace())._build_actor_doc(
        str(actor_id),
        "a",
        snapshot,
        battle_type="arena",
    )
    actor = ActorSnapshot.model_validate(payload)
    actor.meta.tokens["gift"] = 5
    return actor


@pytest.mark.parametrize("skill", [0.0, 0.25, 0.5, 1.0])
async def test_anatomy_from_persisted_skill_increases_executed_heal_once(monkeypatch, skill):
    healer = built_actor(1)
    patient = built_actor(2, anatomy=skill)
    # Hold the only stochastic heal input fixed; retain real catalog, cost,
    # ability preset, resolver, post-process and executor resource commit.
    monkeypatch.setattr(MathCore, "random_range", staticmethod(lambda low, high: low))
    monkeypatch.setattr(MathCore, "roll_chance", staticmethod(lambda chance: (1.0, False)))
    ctx = BattleContext(
        session_id="support-heal",
        actors={"1": healer, "2": patient},
        meta=BattleMeta(
            active=1,
            step_counter=0,
            teams={"a": ["1", "2"]},
            actors_info={"1": "player", "2": "player"},
            active_actors_count=2,
            battle_type="arena",
            location_id="arena",
        ),
    )
    action = CombatActionDTO(
        action_type="instant",
        move=CombatMoveDTO(
            move_id="heal",
            char_id="1",
            strategy="instant",
            payload=InstantPayload(ability_id="heal", target_id="2"),
        ),
    )
    await CombatExecutor()._handle_unidirectional(ctx, action)

    expected = int(50 * (1 + skill))
    assert patient.stats.skills.skill_anatomy == skill
    assert patient.stats.mods.received_healing_bonus == skill
    assert patient.meta.hp == 10 + expected
    results = [task["result"] for task in ctx.pending_result_support_tasks]
    assert len(results) == 1
    assert results[0]["healing_final"] == expected
    assert [
        (fact["actor_id"], fact["delta"])
        for fact in results[0]["resource_facts"]
        if fact["resource"] == "hp" and fact["reason"] == "heal"
    ] == [("2", expected)]


@pytest.fixture
def controlled_attack(monkeypatch):
    resolve = CombatResolver.resolve_exchange

    def run(source, target, ctx):
        ctx.flags.force.hit = True
        ctx.stages.check_crit = False
        return resolve(source, target, ctx)

    monkeypatch.setattr(CombatResolver, "resolve_exchange", staticmethod(run))


async def exchange_and_commit(source, target):
    result = await CombatPipeline().calculate(
        source,
        target,
        CombatMoveDTO(
            move_id="support-strike",
            char_id=source.char_id,
            strategy="exchange",
            payload=ExchangePayload(target_id=target.char_id),
        ),
    )
    MechanicsService().apply_interaction_result(PipelineContextDTO(), source, target, result)
    return result


async def test_anatomy_activity_counts_regen_through_executor_pipeline_and_commit(monkeypatch, controlled_attack):
    source = built_actor(1, anatomy=0.5, attributes={"endurance": 11})
    target = built_actor(2, attributes={"endurance": 11})
    source.meta.hp = source.meta.max_hp - 2
    target.meta.hp = target.meta.max_hp
    monkeypatch.setattr(MathCore, "roll_chance", staticmethod(lambda chance: (1.0, False)))
    ctx = BattleContext(
        session_id="anatomy-activity",
        actors={"1": source, "2": target},
        meta=BattleMeta(
            active=1,
            step_counter=0,
            teams={"a": ["1"], "b": ["2"]},
            actors_info={"1": "player", "2": "player"},
            active_actors_count=2,
            battle_type="arena",
            location_id="arena",
        ),
    )
    action = CombatActionDTO(
        action_type="exchange",
        is_forced=True,
        move=CombatMoveDTO(
            move_id="anatomy-strike",
            char_id="1",
            strategy="exchange",
            payload=ExchangePayload(target_id="2"),
        ),
    )
    executor = CombatExecutor()
    await executor._handle_exchange(ctx, action)
    await executor._handle_exchange(ctx, action)

    assert source.meta.hp == source.meta.max_hp
    assert source.xp_buffer["combat_hp_regenerated"] == 2
    assert source.skills["skill_anatomy"] == 0.5
    saved = source.model_dump(mode="json", exclude={"stats"})
    assert ActorSnapshot.model_validate(saved).xp_buffer["combat_hp_regenerated"] == 2


@pytest.mark.parametrize("skill,dodged", [(0.0, False), (0.25, False), (0.5, True), (1.0, True)])
async def test_tactics_attribute_evasion_changes_real_dodge(monkeypatch, controlled_attack, skill, dodged):
    source = built_actor(1)
    target = built_actor(2, tactics=skill, attributes={"agility": 11})
    monkeypatch.setattr(MathCore, "roll_chance", staticmethod(lambda chance: (0.30, chance > 0.30)))
    result = await exchange_and_commit(source, target)
    trace = next(check for check in result.checks if check.stage == "evasion")
    assert trace.chance == pytest.approx(0.22 * (1 + skill), abs=0.0001)
    assert result.is_dodged is dodged
    # Bonus-token rolls may award another token; only the dodge outcome matters.
    assert bool(target.meta.tokens.get("dodge", 0)) is dodged


@pytest.mark.parametrize("skill,dodged", [(0.0, True), (0.25, True), (0.5, False), (1.0, False)])
async def test_tactics_attribute_anti_evasion_prevents_real_dodge(monkeypatch, controlled_attack, skill, dodged):
    source = built_actor(1, tactics=skill, attributes={"perception": 5.5})
    target = built_actor(2, attributes={"agility": 11})
    monkeypatch.setattr(MathCore, "roll_chance", staticmethod(lambda chance: (0.05, chance > 0.05)))
    result = await exchange_and_commit(source, target)
    trace = next(check for check in result.checks if check.stage == "evasion")
    assert source.stats.mods.anti_dodge_chance == pytest.approx(0.0825 * (1 + 3 * skill), abs=0.0001)
    assert trace.chance == pytest.approx(max(0, 0.22 - source.stats.mods.anti_dodge_chance), abs=0.0001)
    assert result.is_dodged is dodged


@pytest.mark.parametrize("skill,counter", [(0.0, False), (0.25, False), (0.5, True), (1.0, True)])
async def test_tactics_counter_roll_after_actual_light_armor_dodge(monkeypatch, controlled_attack, skill, counter):
    source = built_actor(1)
    target = built_actor(2, tactics=skill, attributes={"agility": 11, "memory": 11, "prediction": 11}, light_armor=True)
    monkeypatch.setattr(MathCore, "roll_chance", staticmethod(lambda chance: (0.0, chance > 0)))
    counter_rolls = []

    def check(chance):
        counter_rolls.append(chance)
        return chance > 0.10

    monkeypatch.setattr(MathCore, "check_chance", staticmethod(check))
    result = await exchange_and_commit(source, target)
    expected = 0.044 * (1 + 4 * skill)
    assert target.loadout.layout["body"] == "skill_light_armor"
    assert result.is_dodged
    assert target.stats.mods.counter_attack_chance == pytest.approx(expected, abs=0.0001)
    assert counter_rolls[-1] == pytest.approx(expected, abs=0.0001)
    assert result.chain_events.trigger_counter_attack is counter
