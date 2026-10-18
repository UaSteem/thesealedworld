import pytest

from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
from src.backend.features.monsters.encounters.policies.composition import MonsterCompositionPolicyResolver
from src.backend.features.monsters.encounters.profiles.registry import get_profile
from src.backend.features.monsters.encounters.services.squad_selection_service import MonsterEncounterSelectionService


@pytest.mark.parametrize("kind", ["ordinary", "patrol", "guard", "leader"])
@pytest.mark.parametrize("difficulty", ["easy", "normal", "hard"])
def test_builtin_goblin_total_limit_applies_to_every_rank(kind, difficulty):
    order = MonsterEncounterOrderDTO(
        encounter_type=kind,
        difficulty=difficulty,
        location_tier=0,
        family_ids=("goblin_tribe",),
        seed=13,
        player_gear_score=100,
    )
    resolver = MonsterCompositionPolicyResolver()
    profile = resolver.profile(order)
    assert (profile.min_members, profile.max_members) == (3, 6)
    service = MonsterEncounterSelectionService()
    pool = service.build_pool(order)
    assert pool.status == "prepared"
    assert all(3 <= len(roster) <= 6 for group in pool.groups for roster in group.variants)
    result = service.select_from_pool(order, pool)
    assert result.status == "selected"
    assert 3 <= len(result.selection.members) <= 6
    if kind != "ordinary":
        assert any(member.role != "minion" for member in result.selection.members)


def test_external_goblin_profile_keeps_explicit_count_and_different_cache_identity():
    order = MonsterEncounterOrderDTO(
        encounter_type="ordinary",
        difficulty="hard",
        location_tier=0,
        family_ids=("goblin_tribe",),
        seed=13,
        player_gear_score=100,
    )
    external = order.model_copy(update={"profile_override": get_profile("solo", "ordinary", "hard")})
    resolver = MonsterCompositionPolicyResolver()
    assert resolver.profile(external).max_members == 8
    service = MonsterEncounterSelectionService()
    assert service.cache_identity(order) != service.cache_identity(external)
    pool = service.build_pool(external)
    assert max(len(roster) for group in pool.groups for roster in group.variants) == 8
