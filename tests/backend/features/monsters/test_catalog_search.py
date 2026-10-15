from dataclasses import FrozenInstanceError, replace

import pytest

from src.backend.features.monsters.catalog.indexes import MonsterCatalog
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.catalog.search import CatalogSearchService, MonsterSearchFilters


def test_default_search_returns_all_ordinary_members_in_registry_order():
    catalog = get_catalog()
    expected = tuple(m for m in catalog.members.values() if catalog.clans[m.clan_id].normal_spawn)
    assert CatalogSearchService().search() == expected
    assert CatalogSearchService().search(MonsterSearchFilters(include_system=True)) == tuple(catalog.members.values())


def test_exact_ids_unknown_ids_and_combined_conditions():
    catalog = get_catalog()
    member = next(m for m in catalog.members.values() if m.family_id == "wolf_pack")
    service = CatalogSearchService(catalog)
    filters = MonsterSearchFilters(family_ids=(member.family_id,), clan_ids=(member.clan_id,), member_ids=(member.id,))
    assert service.search(filters) == (member,)
    assert service.search(replace(filters, family_ids=("missing",))) == ()
    assert service.search(MonsterSearchFilters(member_ids=("missing",))) == ()
    assert service.search(MonsterSearchFilters(member_ids=("missing", member.id))) == (member,)


def test_tags_include_family_clan_and_member_and_require_all():
    original = get_catalog()
    member = next(m for m in original.members.values() if m.family_id == "wolf_pack")
    old_family = original.families[member.family_id]
    family = replace(
        old_family,
        tags=frozenset({"family_only"}),
        mechanics={**old_family.mechanics, "default_tags": ("family_only",)},
    )
    clan = replace(original.clans[member.clan_id], tags=frozenset({"clan_only"}))
    members = {
        m.id: replace(m, tags=family.tags | clan.tags | frozenset(m.mechanics["extra_tags"]))
        if m.family_id == family.id
        else m
        for m in original.members.values()
    }
    enriched = replace(
        member,
        tags=family.tags | clan.tags | {"member_only"},
        mechanics={**member.mechanics, "extra_tags": ("member_only",)},
    )
    catalog = MonsterCatalog(
        {**original.families, family.id: family},
        {**original.clans, clan.id: clan},
        {**members, member.id: enriched},
    )
    service = CatalogSearchService(catalog)
    filters = MonsterSearchFilters(required_tags=("family_only", "clan_only", "member_only"))
    assert service.search(filters) == (enriched,)
    assert service.search(MonsterSearchFilters(required_tags=("member_only",), excluded_tags=("clan_only",))) == ()
    assert service.search(replace(filters, required_tags=("missing",))) == ()


def test_system_member_needs_explicit_permission_even_by_id():
    catalog = get_catalog()
    member = next(m for m in catalog.members.values() if not catalog.clans[m.clan_id].normal_spawn)
    service = CatalogSearchService(catalog)
    assert service.search(MonsterSearchFilters(member_ids=(member.id,))) == ()
    assert service.search(MonsterSearchFilters(member_ids=(member.id,), include_system=True)) == (member,)


@pytest.mark.parametrize("field", ["family_ids", "clan_ids", "member_ids", "required_tags", "excluded_tags"])
def test_filters_reject_bare_strings_and_invalid_entries(field):
    with pytest.raises(TypeError):
        MonsterSearchFilters(**{field: "wolf_pack"})
    with pytest.raises(ValueError):
        MonsterSearchFilters(**{field: ("",)})
    with pytest.raises(TypeError):
        MonsterSearchFilters(**{field: (1,)})


def test_filters_own_immutable_copy_and_reject_conflicting_tags():
    ids = ["wolf_pack"]
    filters = MonsterSearchFilters(family_ids=ids)
    ids.append("rat_swarm")
    assert filters.family_ids == ("wolf_pack",)
    with pytest.raises(FrozenInstanceError):
        filters.include_system = True
    with pytest.raises(ValueError):
        MonsterSearchFilters(required_tags=("beast",), excluded_tags=("beast",))
    catalog = get_catalog()
    members = tuple(catalog.members.items())
    CatalogSearchService(catalog).search(filters)
    assert tuple(catalog.members.items()) == members
