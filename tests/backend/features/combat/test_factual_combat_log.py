"""The public report must work without any artistic event templates."""

import json

import pytest

from src.backend.features.combat.dto.action import CombatActionDTO, CombatMoveDTO, ExchangePayload
from src.backend.features.combat.dto.actor import ActorMetaDTO, ActorSnapshot
from src.backend.features.combat.dto.pipeline import CombatEffectFactDTO, InteractionResultDTO
from src.backend.features.combat.dto.session import BattleContext, BattleMeta
from src.backend.features.combat.integrations import CombatCatalogIntegrator
from src.backend.features.combat.runtime.support.log_builder import CombatLogBuilder
from src.backend.features.game_catalog.combat.resources.common.descriptions import (
    CombatDescriptionDTO,
    build_combat_description,
)


def context():
    actors = {
        str(i): ActorSnapshot(meta=ActorMetaDTO(id=i, name=name, type="player", team=team, hp=100, max_hp=100), raw={})
        for i, name, team in ((1, "Воин", "a"), (2, "Гоблин", "b"))
    }
    return BattleContext(session_id="facts", meta=BattleMeta(
        active=1, step_counter=0, active_actors_count=2, teams={"a": [1], "b": [2]},
        actors_info={"1": "player", "2": "ai"}, battle_type="arena", location_id="arena",
    ), actors=actors)


def action(feint_id=None):
    return CombatActionDTO(action_type="exchange", move=CombatMoveDTO(
        move_id="facts-1", char_id=1, strategy="exchange", payload=ExchangePayload(target_id=2, feint_id=feint_id),
    ))


@pytest.fixture
def forbid_narrative(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("factual report requested an artistic template")
    monkeypatch.setattr(CombatCatalogIntegrator, "get_combat_text_template", forbidden)
    monkeypatch.setattr(CombatDescriptionDTO, "resolve_event_template", forbidden)


@pytest.mark.unit
@pytest.mark.parametrize("outcome", ["hit", "crit", "miss", "dodge", "parry", "block", "heal"])
def test_report_uses_facts_without_narrative(forbid_narrative, outcome):
    result = InteractionResultDTO(source_id=1, target_id=2)
    if outcome == "heal":
        result.healing_final = 18
    else:
        setattr(result, {"hit": "is_hit", "crit": "is_crit", "miss": "is_miss", "dodge": "is_dodged",
                         "parry": "is_parried", "block": "is_blocked"}[outcome], True)
    if outcome in {"hit", "crit", "block"}:
        result.is_hit = True
        result.damage_final = 24
    line = CombatLogBuilder.build_result_entries(ctx=context(), result=result, action=action(), wave=1, timestamp=0)[0]
    assert line["format"] == "factual-v1"
    assert "Воин" in line["text"] and "Гоблин" in line["text"]
    assert line["numbers"]["damage"] == result.damage_final
    assert line["numbers"]["healing"] == result.healing_final
    assert line["template"]["taxonomy"] == "factual"


@pytest.mark.unit
def test_effect_report_does_not_resolve_body_variant(forbid_narrative):
    result = InteractionResultDTO(source_id=1, target_id=2, effect_facts=[
        CombatEffectFactDTO(actor_id=2, owner="target", effect_id="stun", action="apply"),
    ])
    line = CombatLogBuilder.build_effect_fact_entries(ctx=context(), result=result, action=action(), wave=1, timestamp=0)[0]
    assert line["format"] == "factual-v1"
    assert "Гоблин" in line["text"]
    assert line["effects"][0]["effect_id"] == "stun"


@pytest.mark.unit
def test_description_builder_accepts_no_event_texts():
    description = build_combat_description(resource_type="feint", resource_id="new_feint", display_name="Новый финт",
                                           short_description="Механическое назначение")
    assert description.variants["humanoid"].display_name == "Новый финт"
    assert description.variants["humanoid"].event_texts.hit == []
    assert description.variants["beast"].event_texts.hit == []


@pytest.mark.unit
def test_report_public_contract_roundtrip(forbid_narrative):
    from src.backend.features.combat.services.view_service import CombatViewService
    line = CombatLogBuilder.build_result_entries(ctx=context(), result=InteractionResultDTO(
        source_id=1, target_id=2, is_hit=True, damage_final=24, reflected_damage=3,
    ), action=action(), wave=1, timestamp=0)[0]
    event = CombatViewService.parse_logs([json.dumps(line)])[0]
    assert event.format == "factual-v1"
    assert event.numbers.damage == 24
    assert event.numbers.reflected == 3
    assert event.source.id == "1" and event.target.id == "2"


@pytest.mark.unit
def test_trigger_uses_name_and_facts_without_narrative(forbid_narrative, monkeypatch):
    monkeypatch.setattr(CombatLogBuilder, "_trigger_display_policy", lambda *args: "separate")
    result = InteractionResultDTO(source_id=1, target_id=2, is_hit=True, damage_final=24,
                                  fired_triggers=["counter_on_parry"])
    entries = CombatLogBuilder.build_result_entries(ctx=context(), result=result, action=action(), wave=1, timestamp=0)
    assert len(entries) == 2
    assert entries[1]["format"] == "factual-v1"
    assert "срабатывание" in entries[1]["text"]


@pytest.mark.unit
def test_transition_survives_public_roundtrip_without_repeated_apply(forbid_narrative):
    from src.backend.features.combat.dto.pipeline import TacticalTransitionFactDTO
    from src.backend.features.combat.services.view_service import CombatViewService
    result = InteractionResultDTO(source_id=1, target_id=2, tactical_transitions=[TacticalTransitionFactDTO(
        actor_id="1", style="skill_dual_wield", before="normal", after="advantage", reason="initiative",
    )], effect_facts=[CombatEffectFactDTO(actor_id=1, effect_id="tactical_state", action="apply")])
    entries = CombatLogBuilder.build_effect_fact_entries(ctx=context(), result=result, action=action(), wave=3, timestamp=0)
    assert len(entries) == 1
    event = CombatViewService.parse_logs([json.dumps(entries[0])])[0]
    assert event.tactical_transitions[0].after == "advantage"


@pytest.mark.unit
def test_area_report_uses_facts_for_each_target(forbid_narrative):
    line = CombatLogBuilder.build_area_result_entry(ctx=context(), results=[
        InteractionResultDTO(source_id=1, target_id=2, is_hit=True, damage_final=24),
    ], action=action(), wave=1, timestamp=0)
    assert line["format"] == "factual-v1"
    assert "24" in line["text"]


@pytest.mark.unit
@pytest.mark.parametrize("event", ["ON_DODGE", "ON_PARRY", "ON_BLOCK"])
def test_defensive_trigger_is_attributed_to_defender(forbid_narrative, event):
    from src.backend.features.combat.dto.pipeline import CombatTriggerFactDTO
    result = InteractionResultDTO(source_id=1, target_id=2, fired_triggers=["counter_on_parry"], trigger_facts=[
        CombatTriggerFactDTO(trigger_id="counter_on_parry", event=event, display_policy="separate"),
    ])
    entry = CombatLogBuilder._build_trigger_proc_entry(ctx=context(), result=result, trigger_id="counter_on_parry",
        outcome="parry", timestamp=0, tags=[], global_turn=1)
    assert entry["source"]["id"] == "2"
    assert entry["target"]["id"] == "1"


@pytest.mark.unit
def test_absorption_is_public_fact_not_lost_in_private_trace(forbid_narrative):
    from src.backend.features.combat.dto.pipeline import CombatDamageTraceDTO
    result = InteractionResultDTO(source_id=1, target_id=2, is_hit=True, damage_final=24,
        damage_trace=CombatDamageTraceDTO(raw=40, final=24, min=40, max=40,
            details={"shield_absorb": 8, "incoming_damage_absorbed": 3}))
    line = CombatLogBuilder.build_result_entries(ctx=context(), result=result, action=action(), wave=1, timestamp=0)[0]
    assert line["numbers"]["absorbed"] == 11


@pytest.mark.unit
def test_controlled_attempt_keeps_actor_direction_consistent(forbid_narrative):
    result = InteractionResultDTO(source_id=1, target_id=2, skip_reason="controlled")
    line = CombatLogBuilder.build_result_entries(ctx=context(), result=result, action=action(), wave=1, timestamp=0)[0]
    assert line["text"].startswith("Воин → Гоблин:")
    assert line["source"]["name"] == "Воин" and line["target"]["name"] == "Гоблин"
    assert line["outcome"] == "controlled"
