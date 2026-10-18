import pytest
from test_squad_selection_service import order, override

from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


@pytest.mark.parametrize(
    "gs,steps,bonus",
    [(None, 0, 0), (0, 0, 0), (35, 0, 0), (39.99, 0, 0), (40, 1, 3), (45, 2, 6), (50, 3, 9), (100000, 19993, 9)],
)
def test_player_gs_only_adjusts_bounded_point_budget(gs, steps, bonus):
    profile = override(30)
    profile["minions"]["gs_bonus_max"] = 9
    result = MonsterEncounterSelectionService().select(order(player_gear_score=gs, profile_override=profile))
    assert result.budget_bonus == bonus
    assert result.budget_effective == 30 + bonus
    config = result.selection.assembly_input.configuration
    assert config.gs_steps == steps
    assert config.gs_threshold == 35
    assert config.gs_step_size == 5
    assert config.gs_cap_reached == (bonus == 9)
    assert all(m.role == "minion" for m in result.selection.members)


def test_external_profile_uses_literal_threshold_even_on_higher_location_tier():
    profile = override(80)
    profile["minions"].update(gs_threshold=10, gs_step_size=2, gs_points_per_step=4, gs_bonus_max=7)
    result = MonsterEncounterSelectionService().select(
        order(location_tier=1, player_gear_score=14, profile_override=profile)
    )
    config = result.preparation.configurations[0]
    assert (config.gs_threshold, config.gs_steps, config.budget_bonus) == (10, 2, 7)


def test_legacy_single_budget_variants_are_rejected():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        order(profile_override={"id": "legacy", "budget": {"base_points": 80}, "variants": [{"id": "old", "core": {}}]})


@pytest.mark.parametrize("threshold,step,score,expected_steps", [(0.1, 0.1, 0.3, 2), (0, 1e-300, 1e308, 10**608)])
def test_decimal_boundaries_and_large_finite_scores(threshold, step, score, expected_steps):
    profile = override(80)
    profile["minions"].update(gs_threshold=threshold, gs_step_size=step, gs_points_per_step=4, gs_bonus_max=7)
    result = MonsterEncounterSelectionService().select(order(player_gear_score=score, profile_override=profile))
    config = result.preparation.configurations[0]
    assert config.gs_steps == expected_steps
    assert config.budget_bonus == 7
