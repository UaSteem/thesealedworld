import pytest

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator


def test_player_energy_filters_attribute_source_before_multipliers():
    raw = {
        "attributes": {"intellect": {"base": 22}, "mental": {"base": 22}},
        "modifiers": {
            "en_regen": {"base": 1, "source": {"amulet": "+1"}, "temp": {"buff": "*2"}},
            "hp": {"base": 100},
            "hp_regen": {"base": 2},
            "stamina_regen": {"base": 3},
        },
        "rules": {"attribute_profile": "player"},
    }
    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    assert values["combat_en_regen"] == 4
    assert values["en_regen"] > values["combat_en_regen"]
    assert values["combat_hp_regen"] == values["hp_regen"]
    assert values["combat_stamina_regen"] == values["stamina_regen"]


def test_mode_specific_sources_are_independent():
    raw = {
        "modifiers": {
            "hp": {"base": 100},
            "en_regen": {"base": 1},
            "combat_en_regen": {"source": {"battle": "+3"}},
            "outside_en_regen": {"source": {"rest": "+7"}},
        }
    }
    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    assert values["combat_en_regen"] == 4
    assert values["en_regen"] == values["outside_en_regen"] == 8


@pytest.mark.parametrize("role", ["minion", "veteran", "elite", "boss"])
def test_monster_hp_policy_and_energy_modes(role):
    raw = {
        "attributes": {"mental": {"base": 22}},
        "modifiers": {"hp_regen": {"base": 20}, "combat_hp_regen": {"base": 30}, "en_regen": {"base": 1}},
        "rules": {"attribute_profile": "monster:beast"},
        "pipeline": {"role": role},
    }
    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    assert values["combat_hp_regen"] == values["hp_regen"] == 0
    assert values["combat_en_regen"] == values["en_regen"] > 1
