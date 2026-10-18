import pytest

from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator


def raw(profile):
    return {
        "attributes": {},
        "modifiers": {
            "hp": {"base": 100, "source": {"item": 100}, "temp": {"buff": "*2"}},
            "hp_regen": {"base": 2, "source": {"item": 3}, "temp": {}},
            "en_regen": {"base": 4},
            "stamina_regen": {"base": 6},
        },
        "rules": {"attribute_profile": profile},
    }


@pytest.mark.parametrize("profile", ["player", "player:naked", "player:light", "player:medium", "player:heavy"])
def test_player_regen_adds_half_percent_of_final_hp_once(profile):
    source = raw(profile)
    first, _ = StatsWaterfallCalculator.calculate_waterfall(source)
    second, _ = StatsWaterfallCalculator.calculate_waterfall(source)
    assert first["hp_regen"] == pytest.approx(5 + first["hp"] * 0.005)
    assert first == second
    assert first["en_regen"] == 4 and first["stamina_regen"] == 6


@pytest.mark.parametrize("role", ["minion", "veteran", "elite", "boss"])
@pytest.mark.parametrize("profile", ["monster:humanoid", "monster:beast"])
def test_monsters_never_regenerate_hp_even_with_item_bonus(profile, role):
    source = raw(profile)
    source["pipeline"] = {"actor_kind": "monster", "role": role}
    result, _ = StatsWaterfallCalculator.calculate_waterfall(source)
    assert result["hp_regen"] == 0
    assert result["en_regen"] == 4 and result["stamina_regen"] == 6
