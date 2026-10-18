"""Golem natural kits bind saved shared mechanics without generation or database writes."""

from dataclasses import replace

import pytest

from src.backend.features.monsters.catalog.prepared_equipment import (
    get_member_prepared_equipment,
    get_prepared_equipment,
    list_prepared_equipment,
)
from src.backend.features.monsters.catalog.registry import get_catalog
from src.backend.features.monsters.catalog.resources.equipment_mapping import get_natural_equipment_mapping
from src.backend.features.monsters.instances.services.build_readiness import MonsterBuildReadinessService


def test_all_golem_tiers_have_exact_natural_shared_kits():
    catalog = get_catalog()
    members = [member for member in catalog.members.values() if member.family_id == "golem_foundry"]
    assert len(members) == 12
    assert len(list_prepared_equipment(family_id="golem_foundry")) == 72
    readiness = MonsterBuildReadinessService()
    for member in members:
        for tier in range(6):
            kit = get_member_prepared_equipment(member=member, tier=tier)
            assert kit.clan_id == member.clan_id
            assert {slot for slot, value in member.fixed_loadout.items() if value} == {item.slot for item in kit.items}
            for item in kit.items:
                mapping = get_natural_equipment_mapping(member.fixed_loadout[item.slot])
                assert item.generation.natural_key == mapping.natural_key
                assert item.base_id == mapping.base_id
                assert item.generation.source_context["equipment_catalog_id"]
                assert item.generation.source_context["presentation_name_ru"] == mapping.name_ru
                assert item.generation.source_context["presentation_description_ru"] == mapping.description_ru
                assert mapping.name_ru and mapping.description_ru
                assert item.owner_key == f"{member.id}:tier:{tier}"
            report = readiness.check(member=member, family=catalog.families[member.family_id], tier=tier, prepared=kit)
            assert report.ready, report.issues


def test_golem_kit_is_deterministic_and_independent(monkeypatch):
    from src.backend.features.items.services.generation_service import ItemGenerationService

    def forbidden(*args, **kwargs):
        raise AssertionError("Shared golem equipment must not generate items")

    monkeypatch.setattr(ItemGenerationService, "__init__", forbidden)
    kwargs = dict(family_id="golem_foundry", variant_id="stone_worker", tier=0)
    first, second = get_prepared_equipment(**kwargs), get_prepared_equipment(**kwargs)
    assert first == second
    assert first.items[0] is not second.items[0]


@pytest.mark.parametrize("tier", [True, 6, -1])
def test_golem_kit_rejects_unavailable_tiers(tier):
    with pytest.raises((ValueError, LookupError)):
        get_prepared_equipment(family_id="golem_foundry", variant_id="stone_worker", tier=tier)


def test_golem_kit_never_falls_back_to_another_clan():
    member = get_catalog().members["golem_foundry.base.stone_worker"]
    with pytest.raises(LookupError, match="No exact"):
        get_member_prepared_equipment(member=replace(member, clan_id="golem_foundry.iron"), tier=0)
