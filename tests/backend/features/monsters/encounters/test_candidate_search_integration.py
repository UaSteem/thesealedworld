from dataclasses import replace

import pytest

from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.catalog.search import MonsterSearchFilters


@pytest.mark.parametrize("family_id", ("goblin_tribe", "wolf_pack", "rat_swarm", "bandit_gang"))
def test_public_candidate_search_uses_real_catalog_and_prepared_equipment(family_id):
    from src.backend.features.monsters.public import MonsterCandidateSearchService

    result = MonsterCandidateSearchService().search(tier=3, filters=MonsterSearchFilters(family_ids=(family_id,)))
    assert result.candidates
    assert not result.excluded
    assert result.empty_reason is None
    assert all(member.family_id == family_id for member in result.candidates)
    assert result == MonsterCandidateSearchService().search(tier=3, filters=result.filters)


def test_unavailable_tier_is_explained_for_each_real_member():
    from src.backend.features.monsters.public import MonsterCandidateSearchService

    result = MonsterCandidateSearchService().search(tier=6, filters=MonsterSearchFilters(family_ids=("goblin_tribe",)))
    assert not result.candidates
    assert len(result.excluded) == result.matched_count == 12
    assert result.empty_reason == "no_ready_candidates"
    assert not result.unmatched_member_ids
    assert all("tier_unavailable" in {issue.code for issue in report.issues} for report in result.excluded)


def test_one_broken_definition_does_not_hide_other_ready_candidates():
    from src.backend.features.monsters.public import MonsterCandidateSearchService

    original = get_catalog()
    member = original.members["goblin_tribe.base.goblin_sneak"]
    broken = replace(member, ability_ids=("missing_ability",))
    catalog = MonsterCatalog(original.families, original.clans, {**original.members, member.id: broken})
    result = MonsterCandidateSearchService(catalog=catalog).search(
        tier=1,
        filters=MonsterSearchFilters(family_ids=(member.family_id,)),
    )
    assert len(result.candidates) == 11
    assert [report.member_id for report in result.excluded] == [member.id]
    assert "unknown_ability" in {issue.code for issue in result.excluded[0].issues}


def test_candidate_stage_does_not_build_actors_generate_items_or_choose_a_squad(monkeypatch):
    from src.backend.core.calculators.stats_waterfall_calculator import StatsWaterfallCalculator
    from src.backend.features.items.services.generation_service import ItemGenerationService
    from src.backend.features.monsters.encounters.dto.selection import MonsterEncounterOrderDTO
    from src.backend.features.monsters.encounters.policies.group_assembler import MonsterGroupAssembler
    from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder
    from src.backend.features.monsters.public import MonsterCandidateSearchService

    def forbidden(*args, **kwargs):
        pytest.fail("Candidate eligibility must not assemble, generate or calculate combat")

    monkeypatch.setattr(MonsterInstanceBuilder, "build", forbidden)
    monkeypatch.setattr(StatsWaterfallCalculator, "calculate_waterfall", forbidden)
    monkeypatch.setattr(ItemGenerationService, "generate_runtime_projections", forbidden)
    monkeypatch.setattr(MonsterGroupAssembler, "assemble", forbidden)
    request = MonsterEncounterOrderDTO(
        encounter_type="ordinary",
        location_tier=1,
        family_ids=("goblin_tribe",),
        seed=17000,
    )
    result = MonsterCandidateSearchService().search(
        tier=request.location_tier, filters=MonsterSearchFilters(family_ids=request.family_ids)
    )
    assert len(result.candidates) == 12  # No count/role selection at this stage.
