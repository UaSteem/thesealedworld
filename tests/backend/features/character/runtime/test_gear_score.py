from copy import deepcopy

import pytest

from src.backend.features.character.runtime.combat_actor_input import CharacterCombatActorInputBuilder
from src.backend.features.character.runtime.combat_math_model import (
    COMBAT_MODIFIER_KEYS,
    CharacterCombatMathModelBuilder,
)
from src.backend.features.character.runtime.experimental_gear_score import ExperimentalGearScoreCalculator
from src.backend.features.character.runtime.gear_score import CharacterGearScoreCalculator


@pytest.mark.parametrize("mastery", [0.05, 1.0])
def test_live_calculator_matches_accepted_physical_projection(mastery):
    raw = {
        "modifiers": {
            "hp": {"base": 120},
            "armor": {"base": 12},
            "main_hand_damage_base": {"base": 9},
            "off_hand_damage_base": {"base": 7},
        }
    }
    skills = {"skill_fencing": mastery, "skill_dual_wield": mastery, "skill_light_armor": mastery}
    loadout = {
        "layout": {
            "main_hand": "skill_fencing",
            "off_hand": "skill_fencing",
            "tactical_style": "skill_dual_wield",
            "body": "skill_light_armor",
        }
    }
    before = deepcopy((raw, skills, loadout))
    expected = ExperimentalGearScoreCalculator().calculate_from_raw(raw, skills=skills, loadout=loadout)
    actual = CharacterGearScoreCalculator.calculate_from_raw(raw, skills=skills, loadout=loadout)
    assert actual == expected["total"]
    assert (raw, skills, loadout) == before


def test_active_character_uses_same_actor_input_and_preserves_fractional_score():
    active = {"attributes": {"strength": 17, "agility": 15, "endurance": 13}, "items": {}, "skills": {}}
    before = deepcopy(active)
    actor = CharacterCombatActorInputBuilder(CharacterCombatMathModelBuilder()).build_input(active)
    expected = ExperimentalGearScoreCalculator().calculate_from_raw(
        actor["raw"], skills=actor["skills"], loadout=actor["loadout"]
    )
    calculator = CharacterGearScoreCalculator()
    assert calculator.calculate_from_active_character(active) == expected["total"]
    assert calculator.calculate_breakdown_from_active_character(active)["total"] == expected["total"]
    assert active == before


def test_breakdown_preserves_numeric_ui_groups_and_individual_chance_scores():
    values = {
        "hp": 100,
        "armor": 10,
        "main_hand_damage_base": 12,
        "evasion": 0.6,
        "parry": 0.1,
        "combat_hp_regen": 2,
        "combat_en_regen": 1,
        "combat_stamina_regen": 3,
        "anti_dodge_chance": 0.2,
    }
    expected = ExperimentalGearScoreCalculator().calculate_from_calculated(values)
    breakdown = CharacterGearScoreCalculator.calculate_breakdown_from_calculated(values)
    assert all(isinstance(value, (int, float)) for value in breakdown.values())
    assert breakdown["total"] == expected["total"]
    assert breakdown["resources"] == 6
    assert breakdown["skills"] == breakdown["utility"] == 0
    assert breakdown["dodge"] == expected["components"]["extra_ehp"]["parts"]["dodge"]["score"]
    assert breakdown["anti_dodge"] == expected["components"]["extra_offense"]["parts"]["anti_dodge"]["score"]
    assert sum(breakdown[key] for key in ("offense", "defense", "resources", "skills", "utility")) == pytest.approx(
        breakdown["total"], abs=0.001
    )


def test_noncombat_modifiers_and_resource_pools_do_not_add_legacy_points():
    base = CharacterGearScoreCalculator.calculate_from_calculated({"hp": 100})
    modified = CharacterGearScoreCalculator.calculate_from_calculated(
        {"hp": 100, "magic_armor": 900, "en": 900, "stamina": 900, "hand_size": 900, "physical_resistance": 900}
    )
    assert base == modified


@pytest.mark.unit
def test_combat_math_model_outputs_only_combat_modifier_keys() -> None:
    raw = CharacterCombatMathModelBuilder().build_raw(
        attributes={"strength": 10},
        items={
            "layout": {"equipment": {"main_hand": "weapon-1"}},
            "by_id": {
                "weapon-1": {
                    "item_id": "weapon-1",
                    "item_type": "weapon",
                    "mechanics": {
                        "power": 7,
                        "implicit_bonuses": {
                            "main_hand_accuracy_penalty": 0.1,
                            "unknown_bonus": 99,
                        },
                    },
                }
            },
        },
        skills={},
    )

    assert set(raw["modifiers"]) <= COMBAT_MODIFIER_KEYS
    assert "unknown_bonus" not in raw["modifiers"]


@pytest.mark.unit
def test_gear_score_uses_assembled_weapon_power_after_mastery() -> None:
    base_ac = {
        "attributes": {
            "strength": 17,
            "agility": 10,
            "endurance": 8,
        },
        "items": {
            "layout": {"equipment": {"main_hand": "weapon-1"}},
            "by_id": {
                "weapon-1": {
                    "item_id": "weapon-1",
                    "item_type": "weapon",
                    "slot": "main_hand",
                    "mechanics": {
                        "power": 7,
                        "damage_spread": 0.12,
                        "skill_key": "skill_fencing",
                    },
                },
            },
        },
    }
    novice_ac = {**base_ac, "skills": {"skill_fencing": 0.0}}
    master_ac = {**base_ac, "skills": {"skill_fencing": 1.0}}

    calculator = CharacterGearScoreCalculator()

    assert calculator.calculate_from_active_character(master_ac) > calculator.calculate_from_active_character(novice_ac)


@pytest.mark.unit
def test_gear_score_ignores_garment_power_without_combat_modifiers() -> None:
    base_ac = {
        "attributes": {
            "strength": 15,
            "agility": 9,
            "endurance": 16,
            "mental": 13,
        },
        "items": {},
        "skills": {},
    }
    equipped_ac = {
        **base_ac,
        "items": {
            "layout": {"equipment": {"feetwear": "boots-1"}},
            "by_id": {
                "boots-1": {
                    "item_id": "boots-1",
                    "item_type": "garment",
                    "slot": "feetwear",
                    "mechanics": {"power": 8},
                },
            },
        },
    }

    calculator = CharacterGearScoreCalculator()

    assert calculator.calculate_from_active_character(equipped_ac) == calculator.calculate_from_active_character(
        base_ac
    )
