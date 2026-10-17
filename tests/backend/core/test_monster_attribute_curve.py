from copy import deepcopy

import pytest

from src.backend.core.calculators.data.stats_formulas import resolve_attribute_rules
from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator


@pytest.mark.parametrize("profile", ["monster:humanoid", "monster:beast"])
def test_monster_derives_every_modifier_linearly_after_attribute_sources(profile):
    names = [
        "strength",
        "agility",
        "endurance",
        "intellect",
        "memory",
        "mental",
        "perception",
        "projection",
        "prediction",
    ]
    attributes = {
        name: {"base": 50 + i, "source": {"amulet": "+9"}, "temp": {"effect": "+2"}} for i, name in enumerate(names)
    }
    raw = {
        "attributes": attributes,
        "rules": {"attribute_profile": profile},
        "modifiers": {"hp": {"source": {"armor": "+108"}}},
    }
    original = deepcopy(raw)

    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)

    for i, name in enumerate(names):
        assert values[name] == 61 + i
    for target, sources in resolve_attribute_rules(profile).items():
        expected = sum(values[name] * factor for name, factor in sources.items())
        if target == "hp":
            expected += 108
        assert values[target] == pytest.approx(round(expected, 4))
    assert raw == original


@pytest.mark.parametrize(
    "profile",
    [None, "player", "player:naked", "player:light", "player:medium", "player:heavy", "unknown", "monster:unknown"],
)
def test_players_and_unknown_profile_fallback_keep_quadratic_curve(profile):
    raw = {"attributes": {"endurance": {"base": 13, "source": {"ring": "+2"}}}, "rules": {"attribute_profile": profile}}
    values, _ = StatsWaterfallCalculator.calculate_waterfall(raw)
    assert values["endurance"] == 15
    assert values["physical_endurance_power"] == pytest.approx(round(225 / 11, 4))
    assert values["hp"] == pytest.approx(round(225 / 11 * 3, 4))


def test_tier_five_monster_endurance_hp_and_direct_item_modifier():
    values, _ = StatsWaterfallCalculator.calculate_waterfall(
        {
            "attributes": {"endurance": {"base": 68}},
            "rules": {"attribute_profile": "monster:humanoid"},
            "modifiers": {"hp": {"source": {"armor": "+108"}}},
        }
    )
    assert values["hp"] == 312
    assert values["physical_resistance"] == 1.36
