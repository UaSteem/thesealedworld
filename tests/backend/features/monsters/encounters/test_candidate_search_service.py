from dataclasses import FrozenInstanceError, replace

import pytest

from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.catalog.search import MonsterSearchFilters
from src.backend.features.monsters.encounters.services.candidate_search_service import MonsterCandidateSearchService
from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildReadinessService


def test_real_search_preserves_catalog_order_and_definition_identity(monkeypatch):
    from src.backend.features.monsters.instances.services.instance_builder import MonsterInstanceBuilder

    def forbidden(*args, **kwargs):
        raise AssertionError("Search must not build or calculate")

    monkeypatch.setattr(MonsterInstanceBuilder, "build", forbidden)
    monkeypatch.setattr(MonsterInstanceBuilder, "_calculate", forbidden)
    catalog = get_catalog()
    filters = MonsterSearchFilters(family_ids=("goblin_tribe",))
    result = MonsterCandidateSearchService(catalog).search(tier=0, filters=filters)
    expected = tuple(m for m in catalog.members.values() if m.family_id == "goblin_tribe")
    assert result.candidates == expected
    assert all(a is b for a, b in zip(result.candidates, expected, strict=True))
    assert result.filters is filters
    assert result.matched_count == 12
    assert result.empty_reason is None
    assert not result.excluded
    with pytest.raises(FrozenInstanceError):
        result.tier = 1


def test_mixed_readiness_keeps_full_reports_and_does_not_prefilter_tier():
    catalog = get_catalog()
    first, second = tuple(m for m in catalog.members.values() if m.family_id == "goblin_tribe")[:2]
    changed = replace(
        second, min_tier=1, mechanics={**second.mechanics, "min_tier": 1}, ability_ids=("missing_ability",)
    )
    members = dict(catalog.members)
    members[second.id] = changed
    catalog = MonsterCatalog(catalog.families, catalog.clans, members)
    filters = MonsterSearchFilters(member_ids=(first.id, second.id))
    result = MonsterCandidateSearchService(catalog).search(tier=0, filters=filters)
    assert result.candidates == (first,)
    assert result.matched_count == 2
    assert result.excluded[0].member_id == second.id
    assert {i.code for i in result.excluded[0].issues} == {"tier_unavailable", "unknown_ability"}
    assert not result.unmatched_member_ids


def test_no_ready_candidates_differs_from_no_matches():
    service = MonsterCandidateSearchService()
    rejected = service.search(tier=7, filters=MonsterSearchFilters(family_ids=("goblin_tribe",)))
    assert rejected.empty_reason == "no_ready_candidates"
    assert rejected.matched_count == 12
    assert len(rejected.excluded) == 12
    absent = service.search(tier=0, filters=MonsterSearchFilters(member_ids=("missing", "missing")))
    assert absent.empty_reason == "no_catalog_matches"
    assert absent.unmatched_member_ids == ("missing",)


@pytest.mark.parametrize("tier", (True, False, -1, 8, 1.0, "1", None))
def test_invalid_tier_fails_before_dependencies(tier):
    class Forbidden:
        def check(self, **kwargs):
            raise AssertionError("Dependency must not run")

    with pytest.raises(ValueError):
        MonsterCandidateSearchService(catalog=object(), readiness=Forbidden()).search(tier=tier)


def test_wrong_filters_fail_before_dependencies():
    with pytest.raises(TypeError):
        MonsterCandidateSearchService(catalog=object()).search(tier=0, filters={})


def test_missing_ids_mean_not_matched_under_filters():
    member_id = "goblin_tribe.base.goblin_sneak"
    filters = MonsterSearchFilters(member_ids=(member_id, "missing", member_id), family_ids=("wolf_pack",))
    result = MonsterCandidateSearchService().search(tier=0, filters=filters)
    assert result.unmatched_member_ids == (member_id, "missing")


def test_system_members_stay_excluded_unless_requested():
    catalog = get_catalog()
    member = next(m for m in catalog.members.values() if not catalog.clans[m.clan_id].normal_spawn)
    service = MonsterCandidateSearchService(catalog)
    default = service.search(tier=0, filters=MonsterSearchFilters(member_ids=(member.id,)))
    assert default.empty_reason == "no_catalog_matches"
    explicit = service.search(tier=0, filters=MonsterSearchFilters(member_ids=(member.id,), include_system=True))
    assert explicit.matched_count == 1
    assert not explicit.unmatched_member_ids


def test_injected_readiness_report_is_retained_and_unexpected_errors_propagate():
    catalog = get_catalog()
    member = catalog.members["goblin_tribe.base.goblin_sneak"]
    report = MonsterBuildReadinessService().check(member=member, family=catalog.families[member.family_id], tier=7)

    class Readiness:
        def check(self, **kwargs):
            assert kwargs == dict(member=member, family=catalog.families[member.family_id], tier=7)
            return report

    filters = MonsterSearchFilters(member_ids=(member.id,))
    result = MonsterCandidateSearchService(catalog, Readiness()).search(tier=7, filters=filters)
    assert result.excluded[0] is report

    class Broken:
        def check(self, **kwargs):
            raise RuntimeError("unexpected")

    with pytest.raises(RuntimeError, match="unexpected"):
        MonsterCandidateSearchService(catalog, Broken()).search(tier=0, filters=filters)


def test_default_catalog_is_resolved_once_per_search(monkeypatch):
    from src.backend.features.monsters.catalog import registry
    from src.backend.features.monsters.catalog.search import CatalogSearchService

    catalog = get_catalog()
    calls = []

    def resolve():
        calls.append(True)
        return catalog

    monkeypatch.setattr(registry, "get_catalog", resolve)
    filters = MonsterSearchFilters(
        family_ids=("goblin_tribe",), required_tags=tuple(catalog.families["goblin_tribe"].tags)[:1]
    )
    result = MonsterCandidateSearchService().search(tier=0, filters=filters)
    assert len(calls) == 1
    assert result.candidates == CatalogSearchService(catalog).search(filters)
    assert len(calls) == 1
