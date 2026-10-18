import pytest
from pydantic import ValidationError

from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.policies.composition import MonsterCompositionPolicyResolver
from src.backend.features.monsters.encounters.profiles.contracts import MonsterAssemblyProfileDTO
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


def test_builtin_minion_budget_requires_player_gs():
    result = MonsterEncounterSelectionService().select(
        MonsterEncounterOrderDTO(encounter_type="ordinary", location_tier=0, family_ids=("goblin_tribe",), seed=1)
    )
    assert result.status == "rejected"
    assert result.reasons[0].code == "player_gear_score_required"


def profile():
    return MonsterAssemblyProfileDTO.model_validate(
        {
            "id": "relative",
            "minions": {"mode": "relative_gs", "reference_gs": 40, "base_points": 30, "gs_bonus_max": 9},
            "seniors": {"base_points": 0},
            "roles": [{"role": "minion", "min_count": 0, "max_count": 8}],
        }
    )


@pytest.mark.parametrize(
    "gs,effective,scaled,bonus",
    [
        (0, 0, 0, 0),
        (20, 15, 15, 0),
        (39.999, 29, 29, 0),
        (40, 30, 30, 0),
        (41.4, 31, 30, 1),
        (52, 39, 30, 9),
        (10000, 39, 30, 9),
    ],
)
def test_relative_budget_scales_down_and_caps_without_steps(gs, effective, scaled, bonus):
    order = MonsterEncounterOrderDTO(
        encounter_type="ordinary", location_tier=0, family_ids=("goblin_tribe",), seed=1, player_gear_score=gs
    )
    pool = MonsterCompositionPolicyResolver().resolve(order=order, profile=profile())[0].minions
    assert (pool.effective_points, pool.scaled_points, pool.bonus_points) == (effective, scaled, bonus)
    assert pool.gs_steps == 0
    assert pool.player_gs_ratio == pytest.approx(gs / 40)


def test_missing_gs_rejected_before_candidate_search():
    from src.backend.features.monsters.encounters.services.encounter_preparation_service import (
        MonsterEncounterPreparationService,
    )

    class Forbidden:
        def search(self, **kwargs):
            pytest.fail("search must not run")

    order = MonsterEncounterOrderDTO(encounter_type="ordinary", location_tier=0, family_ids=("goblin_tribe",), seed=1)
    result = MonsterEncounterPreparationService(candidate_search=Forbidden()).prepare(order)
    assert result.reasons[0].code == "player_gear_score_required"


def test_relative_reference_must_be_positive_finite():
    for reference in (None, 0, -1, True, float("inf")):
        data = profile().model_dump()
        data["minions"]["reference_gs"] = reference
        with pytest.raises(ValidationError):
            MonsterAssemblyProfileDTO.model_validate(data)


def test_zero_gs_has_no_hidden_minimum_budget():
    result = MonsterEncounterSelectionService().select(
        MonsterEncounterOrderDTO(
            encounter_type="ordinary", location_tier=0, family_ids=("goblin_tribe",), seed=1, player_gear_score=0
        )
    )
    assert result.status == "rejected"
    assert result.minions.effective_points == result.minions.scaled_points == 0


def test_relative_minion_surplus_cannot_pay_required_seniors():
    data = profile().model_dump()
    data["minions"].update(base_points=120, gs_bonus_max=0)
    data["roles"] = (*data["roles"], {"role": "veteran", "min_count": 1, "max_count": 3})
    order = MonsterEncounterOrderDTO(
        encounter_type="patrol",
        location_tier=0,
        family_ids=("goblin_tribe",),
        seed=1,
        player_gear_score=40,
        profile_override=data,
    )
    result = MonsterEncounterSelectionService().select(order)
    assert result.status == "rejected"
    assert any(reason.path == "seniors" for attempt in result.attempts for reason in attempt.reasons)


def test_senior_steps_are_unchanged_under_relative_minions():
    from src.backend.features.monsters.encounters.profiles.registry import get_profile

    order = MonsterEncounterOrderDTO(
        encounter_type="patrol", location_tier=0, family_ids=("goblin_tribe",), seed=1, player_gear_score=45
    )
    config = MonsterCompositionPolicyResolver().resolve(order=order, profile=get_profile("solo", "patrol", "easy"))[0]
    assert config.minions.mode == "relative_gs" and config.minions.gs_steps == 0
    assert config.seniors.mode == "fixed"
    assert (config.seniors.gs_steps, config.seniors.bonus_points) == (2, 10)
