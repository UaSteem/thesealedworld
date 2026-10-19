"""Compare actual priced compositions, not only authored budget numbers."""

from collections import Counter

import pytest

from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


@pytest.mark.parametrize("kind", ["ordinary", "patrol", "guard", "leader"])
@pytest.mark.parametrize("score", [None, 40, 45, 50, 1000])
def test_goblin_difficulties_increase_available_budget_and_keep_required_core(kind, score):
    service = MonsterEncounterSelectionService()
    for seed in range(5):
        results = [
            service.select(
                MonsterEncounterOrderDTO(
                    encounter_type=kind,
                    difficulty=difficulty,
                    location_tier=0,
                    family_ids=("goblin_tribe",),
                    seed=seed,
                    player_gear_score=36.326 if score is None else score,
                )
            )
            for difficulty in ("easy", "normal", "hard")
        ]
        assert all(result.status == "selected" for result in results)
        assert results[0].budget_effective < results[1].budget_effective < results[2].budget_effective
        # Seeded selection keeps every largest/previous-size variant, not only
        # maximum-spend rosters. More budget need not increase selected spend.
        for result in results:
            config = result.selection.assembly_input.configuration
            ranks = Counter(member.role for member in result.selection.members)
            assert 3 <= len(result.selection.members) <= 6
            assert set(ranks) <= {rule.role for rule in config.roles}
            for pool_name in ("minions", "seniors"):
                pool = getattr(result, pool_name)
                assert pool.spent_points <= pool.effective_points
            for rule in config.roles:
                assert rule.min_count <= ranks[rule.role] <= rule.max_count


def test_unaffordable_family_returns_reason_instead_of_changing_budget():
    result = MonsterEncounterSelectionService().select(
        MonsterEncounterOrderDTO(
            encounter_type="ordinary",
            difficulty="easy",
            location_tier=2,
            family_ids=("golem_foundry",),
            seed=13,
            player_gear_score=36.326,
            profile_override={
                "id": "test.unaffordable",
                "minions": {"base_points": 1},
                "seniors": {"base_points": 0},
                "roles": [{"role": "minion", "max_count": 3}],
                "min_members": 2, "max_members": 3,
            },
        )
    )
    assert result.status == "rejected"
    assert result.reasons
    assert result.preparation.configurations[0].budget_effective == 1

    assert any(reason.code == "squad_minimum_unaffordable" for attempt in result.attempts for reason in attempt.reasons)
