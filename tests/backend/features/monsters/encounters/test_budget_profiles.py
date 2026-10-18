import pytest
from pydantic import ValidationError

from src.backend.features.monsters.encounters.profiles.contracts import MonsterAssemblyProfileDTO
from src.backend.features.monsters.encounters.profiles.registry import get_profile


def test_budget_profile_registry_is_organization_independent():
    profile = get_profile("solo", "patrol", "easy")
    assert next(role for role in profile.roles if role.role == "veteran").min_count == 1
    assert profile.minions.base_points > 0
    assert profile.seniors.base_points > 0
    assert get_profile("group", "patrol", "easy") is None


@pytest.mark.parametrize(
    "changes",
    [
        {"min_members": 4, "max_members": 2},
        {"max_members": 9},
        {"roles": []},
        {"minions": {"base_points": -1}},
        {"minions": {"base_points": True}},
        {"minions": {"base_points": 80, "gs_bonus_max": -1}},
        {"minions": {"base_points": 80, "gs_threshold": True}},
        {"minions": {"base_points": 80, "gs_threshold": -1}},
        {"minions": {"base_points": 80, "gs_step_size": 0}},
        {"minions": {"base_points": 80, "gs_step_size": "5"}},
        {"minions": {"base_points": 80, "gs_step_size": float("inf")}},
        {"minions": {"base_points": 80, "gs_threshold": float("nan")}},
        {"minions": {"base_points": 80, "gs_points_per_step": True}},
        {"minions": {"base_points": 80, "gs_points_per_step": -1}},
        {"minions": {"base_points": 80, "reference_player_gs": "260"}},
        {"roles": [{"role": "minion", "min_count": 1, "max_count": 9}]},
        {"roles": [{"role": "minion", "min_count": 1, "max_count": 2}] * 2},
    ],
)
def test_invalid_profile_rejected_at_boundary(changes):
    data = get_profile("solo", "ordinary", "easy").model_dump() | changes
    with pytest.raises(ValidationError):
        MonsterAssemblyProfileDTO.model_validate(data)


@pytest.mark.parametrize(
    "tier,threshold,step",
    [(0, 35, 5), (1, 55, 8), (2, 85, 12), (3, 120, 15), (4, 170, 20), (5, 230, 25), (6, 300, 30), (7, 380, 40)],
)
def test_builtin_tier_references_are_explicit(tier, threshold, step):
    profile = get_profile("solo", "ordinary", "easy", tier)
    assert (profile.seniors.gs_threshold, profile.seniors.gs_step_size) == (threshold, step)
    refs = (36.326, 55.977, 66.664, 119.849, 171.053, 312.108, 508.203, 814.358)
    assert profile.minions.mode == "relative_gs"
    assert profile.minions.reference_gs == refs[tier]


@pytest.mark.parametrize(
    "kind,increments",
    [("ordinary", (3, 5, 7)), ("patrol", (5, 8, 10)), ("guard", (7, 10, 15)), ("leader", (10, 20, 30))],
)
def test_each_type_and_difficulty_has_own_increment_and_cap(kind, increments):
    for i, (difficulty, increment) in enumerate(zip(("easy", "normal", "hard"), increments, strict=True)):
        profile = get_profile("solo", kind, difficulty)
        minions, seniors = profile.minions, profile.seniors
        assert minions.base_points == ((30, 45, 60)[i] if kind == "ordinary" else 30)
        assert minions.gs_points_per_step == 0
        assert minions.gs_bonus_max == ((9, 15, 21)[i] if kind == "ordinary" else 0)
        expected = {"ordinary": (0, 0, 0), "patrol": (23, 46, 69), "guard": (30, 53, 76), "leader": (45, 68, 98)}
        caps = {"ordinary": (0, 0, 0), "patrol": (23, 23, 23), "guard": (23, 30, 30), "leader": (23, 30, 30)}
        assert seniors.base_points == expected[kind][i]
        assert seniors.gs_points_per_step == (0 if kind == "ordinary" else increment)
        assert seniors.gs_bonus_max == caps[kind][i]
