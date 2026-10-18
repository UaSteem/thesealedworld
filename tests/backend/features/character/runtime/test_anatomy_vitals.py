from copy import deepcopy

import pytest

from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
from src.backend.features.character.runtime.vitals import CharacterVitalsCalculator
from src.backend.features.character.schemas.session import CharacterSessionAttributesDTO


@pytest.mark.parametrize("level", [0.25, 0.5, 1.0])
def test_outside_vitals_receive_anatomy_from_flat_and_persisted_skills(level):
    attributes = CharacterSessionAttributesDTO(**{key: 20 for key in CharacterSessionAttributesDTO.model_fields})
    zero = CharacterVitalsCalculator.calculate_max_vitals(attributes, skills={"skill_anatomy": 0.0})
    trained = CharacterVitalsCalculator.calculate_max_vitals(attributes, skills={"skill_anatomy": level})
    nested = CharacterVitalsCalculator.calculate_max_vitals(attributes, skills={"skill_anatomy": {"xp": level}})
    assert trained == nested
    assert trained.hp.regen > zero.hp.regen
    assert trained.energy.regen > zero.energy.regen
    assert trained.stamina == zero.stamina
    assert trained.hp.max == zero.hp.max
    assert trained.energy.max == zero.energy.max


def test_vital_refresh_does_not_accumulate_anatomy_bonus_or_heal_current_hp():
    attributes = CharacterSessionAttributesDTO(**{key: 20 for key in CharacterSessionAttributesDTO.model_fields})
    skills = {"skill_anatomy": {"xp": 0.5}}
    vitals = CharacterVitalsCalculator.build_initial_vitals(attributes, skills=skills)
    vitals.hp.cur = 10
    previous = deepcopy(vitals)
    refreshed = CharacterVitalsCalculator.refresh_max_vitals(vitals, attributes, skills=skills)
    again = CharacterVitalsCalculator.refresh_max_vitals(refreshed, attributes, skills=skills)
    assert previous == refreshed == again


def test_combat_and_outside_hp_regeneration_use_same_anatomy_multiplier():
    from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator

    attributes = CharacterSessionAttributesDTO(**{key: 20 for key in CharacterSessionAttributesDTO.model_fields})
    for level in (0.0, 0.25, 0.5, 1.0):
        skills = {"skill_anatomy": level}
        vitals = CharacterVitalsCalculator.calculate_max_vitals(attributes, skills=skills)
        raw = CharacterCombatActorInputBuilder().build_input({"attributes": attributes.model_dump(), "skills": skills})
        calculated, _ = StatsWaterfallCalculator.calculate_waterfall(raw["raw"])
        assert vitals.hp.regen == pytest.approx(calculated["outside_hp_regen"])
        assert vitals.energy.regen == pytest.approx(calculated["outside_en_regen"])
        assert vitals.stamina.regen == pytest.approx(calculated["outside_stamina_regen"])


@pytest.mark.asyncio
async def test_session_vitals_include_persisted_and_pending_anatomy(fake_redis_service, fake_redis_client):
    from src.backend.infrastructure.actor_state.managers.session import CharacterSessionManager

    attributes = CharacterSessionAttributesDTO(**{key: 20 for key in CharacterSessionAttributesDTO.model_fields})
    zero = CharacterVitalsCalculator.build_initial_vitals(attributes)
    zero.hp.cur = 10
    zero.energy.cur = 10
    fake_redis_client.store["game:ac:7"] = {
        "char_id": 7,
        "attributes": attributes.model_dump(),
        "skills": {"skill_anatomy": {"xp": 0.25}},
        "pending_progress": {"skills": {"skill_anatomy": 0.25}},
        "vitals": zero.model_dump(mode="json"),
    }
    manager = CharacterSessionManager(fake_redis_service)
    refreshed = await manager.refresh_vitals_max(7)
    assert refreshed["vitals"]["hp"]["regen"] == pytest.approx(zero.hp.regen * 2.5, abs=0.0001)
    assert refreshed["vitals"]["energy"]["regen"] == pytest.approx(zero.energy.regen * 2.5, abs=0.0001)
    assert refreshed["vitals"]["hp"]["cur"] == 10
    restored = await manager.restore_vitals_to_max(7)
    assert restored["hp"]["regen"] == refreshed["vitals"]["hp"]["regen"]
    assert restored["hp"]["cur"] == restored["hp"]["max"]


@pytest.mark.parametrize("level", [0.0, 0.25, 0.5, 1.0])
def test_equipment_attribute_bonuses_feed_same_natural_regen_inside_and_outside(level):
    from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator

    attributes = CharacterSessionAttributesDTO(**{key: 11 for key in CharacterSessionAttributesDTO.model_fields})
    items = {
        "layout": {"equipment": {"ring_1": "ring"}},
        "by_id": {
            "ring": {
                "item_id": "ring",
                "item_type": "accessory",
                "slot": "ring_1",
                "mechanics": {"bonuses": {"endurance": "+11", "mental": "+11"}},
            }
        },
    }
    skills = {"skill_anatomy": level}
    vitals = CharacterVitalsCalculator.calculate_max_vitals(attributes, items=items, skills=skills)
    actor = CharacterCombatActorInputBuilder().build_input(
        {"attributes": attributes.model_dump(), "items": items, "skills": skills}
    )
    values, _ = StatsWaterfallCalculator.calculate_waterfall(actor["raw"])
    assert vitals.hp.max == values["hp"]
    assert vitals.hp.regen == pytest.approx(values["outside_hp_regen"])
    assert vitals.energy.regen == pytest.approx(values["outside_en_regen"])
