import pytest

from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.profiles.registry import get_profile
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


def test_ordinary_has_two_independent_pools_and_no_senior_roles():
    for difficulty in ("easy", "normal", "hard"):
        profile = get_profile("solo", "ordinary", difficulty)
        assert profile.minions.base_points > 0
        assert profile.seniors.base_points == 0
        assert {rule.role for rule in profile.roles} == {"minion"}


def select(profile, score=36.326):
    return MonsterEncounterSelectionService().select(
        MonsterEncounterOrderDTO(
            encounter_type="patrol",
            location_tier=0,
            family_ids=("goblin_tribe",),
            seed=7,
            player_gear_score=score,
            profile_override=profile,
        )
    )


@pytest.mark.parametrize("pool", ["minions", "seniors"])
def test_pool_surplus_cannot_pay_other_pool_minimum(pool):
    profile = get_profile("solo", "patrol", "easy").model_dump()
    profile["minions"].update(mode="fixed", reference_gs=None)
    profile["minions"]["base_points"] = 100
    profile["roles"][0]["min_count"] = 2
    profile["roles"][0]["max_count"] = 2
    profile["seniors"]["base_points"] = 100
    profile[pool]["base_points"] = 1
    result = select(profile)
    assert result.status == "rejected"
    assert any(reason.path == pool for attempt in result.attempts for reason in attempt.reasons)


def test_senior_growth_preserves_minion_accompaniment():
    profile = get_profile("solo", "patrol", "easy")
    base, stronger = select(profile), select(profile, 100)
    # Both artifacts contain all largest and previous-size variants; selection need not exhaust money.
    assert base.minions.effective_points == stronger.minions.effective_points == 30
    for result in (base, stronger):
        assert result.minions.spent_points <= 30
        assert result.seniors.spent_points <= result.seniors.effective_points
        assert sum(m.role == "veteran" for m in result.selection.members) >= 1
    assert base.seniors.effective_points == 23
    assert stronger.seniors.effective_points == 46


def test_seniors_are_selected_first_and_minions_only_fill_remaining_slots():
    profile = get_profile("solo", "patrol", "hard").model_dump()
    profile["minions"].update(mode="fixed", reference_gs=None)
    profile["minions"]["base_points"] = 120
    result = select(profile)
    assert result.status == "selected"
    assert len(result.selection.members) in (7, 8)
    assert 1 <= sum(m.role == "veteran" for m in result.selection.members) <= 3
    roles = [member.role for member in result.selection.members]
    assert roles == sorted(roles, key=lambda role: role == "minion")


def test_seniors_can_fill_entire_squad_without_hidden_minion_floor():
    profile = get_profile("solo", "patrol", "easy").model_dump()
    profile["minions"].update(mode="fixed", reference_gs=None)
    profile["minions"]["base_points"] = 0
    profile["seniors"]["base_points"] = 46
    result = select(profile)
    assert result.status == "selected"
    assert [m.role for m in result.selection.members] == ["veteran", "veteran"]
    assert result.minions.spent_points == 0


def test_only_overall_minimum_can_reject_zero_minions():
    profile = get_profile("solo", "patrol", "easy").model_dump()
    profile["minions"].update(mode="fixed", reference_gs=None)
    profile["minions"]["base_points"] = 0
    result = select(profile)
    assert result.status == "rejected"
    assert any(reason.code == "squad_minimum_unaffordable" for attempt in result.attempts for reason in attempt.reasons)


def test_zero_both_pools_is_domain_rejection_not_configuration_exception():
    profile = get_profile("solo", "ordinary", "easy").model_dump()
    profile["minions"].update(mode="fixed", reference_gs=None)
    profile["minions"]["base_points"] = 0
    result = select(profile)
    assert result.status == "rejected"
    assert result.budget_effective == 0
    assert result.minions.effective_points == result.seniors.effective_points == 0


def test_starter_gs_affords_three_current_goblin_minions_without_seniors():
    result = MonsterEncounterSelectionService().select(
        MonsterEncounterOrderDTO(
            encounter_type="ordinary",
            difficulty="easy",
            location_tier=0,
            family_ids=("goblin_tribe",),
            seed=1,
            player_gear_score=28.357,
        )
    )
    assert result.status == "selected"
    assert result.minions.effective_points == 23
    assert result.minions.spent_points <= 23
    assert len(result.selection.members) == 3
    assert all(member.role == "minion" for member in result.selection.members)
    assert result.seniors.effective_points == result.seniors.spent_points == 0
    prices = {
        member.variant_id: member.assembly_cost for member in result.preparation.candidates if member.role == "minion"
    }
    assert prices == {"goblin_scavenger": 7, "goblin_sparkpick": 8, "goblin_sneak": 9, "goblin_cutter": 10}
